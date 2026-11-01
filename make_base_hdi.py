#!/usr/bin/env python3
"""make_base_hdi.py - build a FreeDOS(98) base HDI of a given size without the game engine.

Uses tools_open/base_freedos98_scsi_10m_clean.hdi in this repo as the template:
  1. Parse the whole file tree of the template read-only (FAT16)
  2. Recompute the BPB / partition / FAT16 geometry for the target size
     (adaptive cluster size, still FAT16)
  3. Rebuild a clean image with equivalent content from the template's IPL,
     partition table and boot sector
  4. Read the result back and verify the file tree matches the template

The output can be used directly as the base image for tools_open/ in the Naiz
main project (no game engine included).

Usage:
    ./make_base_hdi.py --size 250M
    ./make_base_hdi.py --size 500M --out build/base_500m.hdi
    ./make_base_hdi.py --size 2G

Size syntax: plain number = bytes, suffix K/M/G (base 1024). The size is rounded
down to whole cylinders (17 sectors * 8 heads * 512 bytes = 69,632 bytes).

Dependencies: Python 3 standard library only.
"""

import argparse
import hashlib
import mmap
import os
import struct
import sys

SECTOR = 512
SPT = 17            # sectors per track (matches the template IPL/BIOS)
HEADS = 8           # number of heads
HDR_SIZE = 4096     # HDI header size
ROOT_ENTRIES = 3072 # root directory entries (same as template, 192 sectors)
RESERVED_SECTORS = 2
NUM_FATS = 2
MEDIA_DESC = 0xF8
SECTOR_PER_CYL = SPT * HEADS
CYL_BYTES = SECTOR_PER_CYL * SECTOR

FAT16_EOC = 0xFFF8
FAT12_EOC = 0x0FF8

ATTR_VOLUME_ID = 0x08
ATTR_DIRECTORY = 0x10
ATTR_LFN = 0x0F


def die(msg):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def parse_size(text):
    """'250M' / '250MB' / '250MiB' / '2G' / plain bytes -> byte count."""
    s = text.strip().upper()
    if s.endswith("B"):
        s = s[:-1]
    if s.endswith("IB"):
        s = s[:-2]
    mult = 1
    if s and s[-1] in "KMG":
        mult = {"K": 1024, "M": 1024 ** 2, "G": 1024 ** 3}[s[-1]]
        s = s[:-1]
    try:
        val = int(s)
    except ValueError:
        die(f"Cannot parse size: {text}")
    if val <= 0:
        die(f"Size must be positive: {text}")
    return val * mult


class TemplateFat:
    """Read-only FAT parser for the template HDI (FAT12/16 only; template is FAT16)."""

    def __init__(self, path):
        self.path = path
        self._f = open(path, "rb")
        size = os.path.getsize(path)
        if size < HDR_SIZE + SECTOR:
            die(f"Template too small: {path}")
        self._mm = mmap.mmap(self._f.fileno(), 0, access=mmap.ACCESS_READ)

        hdr = struct.unpack_from("<8I", self._mm, 0)
        self.header_size = hdr[2]
        self.data_size = hdr[3]
        self.sec_size = hdr[4]
        self.spt = hdr[5]
        self.heads = hdr[6]
        self.cyls = hdr[7]
        if self.sec_size != SECTOR or self.header_size != HDR_SIZE:
            die("Template is not 512-byte sectors / 4096-byte HDI header, unsupported")
        self.part_offset = self._find_partition()
        self._parse_vbr()
        self._parse_fat()
        self.root = self._read_tree()

    # ---- internals ----
    def _read(self, off, length):
        if off < 0 or off + length > len(self._mm):
            raise ValueError(f"Out-of-range read off={off} len={length}")
        return self._mm[off:off + length]

    def _sector(self, lba):
        return self._read(self.header_size + lba * SECTOR, SECTOR)

    def _find_partition(self):
        sec1 = self._sector(1)
        # First partition entry: start CHS at entry offsets 4..7 (98Bridge detection layout)
        e = sec1[0:32]
        head = e[4]
        sec = e[5] or 1
        cyl = struct.unpack_from("<H", e, 6)[0]
        lba = cyl * self.heads * self.spt + head * self.spt + (sec - 1)
        if lba <= 0:
            die("Invalid template partition table (start LBA = 0)")
        return lba * SECTOR

    def _parse_vbr(self):
        self.vbr = self._read(self.header_size + self.part_offset, SECTOR)
        if self.vbr[0] not in (0xEB, 0xE9):
            die("Invalid template partition boot sector (no jmp)")
        self.bytes_per_sector = struct.unpack_from("<H", self.vbr, 0x0B)[0]
        self.spc = self.vbr[0x0D]
        self.reserved = struct.unpack_from("<H", self.vbr, 0x0E)[0]
        self.num_fats = self.vbr[0x10]
        self.root_entries = struct.unpack_from("<H", self.vbr, 0x11)[0]
        self.total16 = struct.unpack_from("<H", self.vbr, 0x13)[0]
        self.total32 = struct.unpack_from("<I", self.vbr, 0x20)[0]
        self.total_sectors = self.total16 or self.total32
        self.fat_sectors = struct.unpack_from("<H", self.vbr, 0x16)[0]
        if self.fat_sectors == 0:
            die("Template is FAT32, unsupported")
        self.root_sectors = (self.root_entries * 32 + SECTOR - 1) // SECTOR
        self.fat_offset = self.part_offset + self.reserved * SECTOR
        self.root_offset = (self.fat_offset + self.num_fats * self.fat_sectors * SECTOR)
        self.data_offset = self.root_offset + self.root_sectors * SECTOR
        self.cluster_size = self.spc * SECTOR
        data_secs = (self.total_sectors - self.reserved
                     - self.num_fats * self.fat_sectors - self.root_sectors)
        clusters = data_secs // self.spc
        self.fat_type = 12 if clusters < 4085 else 16
        self.max_cluster = clusters + 2

    def _parse_fat(self):
        self.fat_data = self._read(self.header_size + self.fat_offset,
                                   self.fat_sectors * SECTOR)

    def _fat_entry(self, c):
        if self.fat_type == 12:
            off = c + (c // 2)
            if off + 1 >= len(self.fat_data):
                return FAT12_EOC
            word = struct.unpack_from("<H", self.fat_data, off)[0]
            return (word >> 4) if (c & 1) else (word & 0x0FFF)
        off = c * 2
        if off + 2 > len(self.fat_data):
            return FAT16_EOC
        return struct.unpack_from("<H", self.fat_data, off)[0]

    def _chain(self, start):
        eoc = FAT12_EOC if self.fat_type == 12 else FAT16_EOC
        out, c, seen = [], start, set()
        while 2 <= c < eoc and c not in seen:
            seen.add(c)
            out.append(c)
            c = self._fat_entry(c)
        return out

    def read_cluster_bytes(self, cluster, count):
        off = self.header_size + self.data_offset + (cluster - 2) * self.cluster_size
        return self._read(off, count * self.cluster_size)

    def _read_dir(self, cluster, is_root=False, size=0):
        if is_root:
            data = self._read(self.header_size + self.root_offset,
                              self.root_sectors * SECTOR)
        else:
            chain = self._chain(cluster)
            data = b"".join(self.read_cluster_bytes(c, 1) for c in chain)
            data = data[:size] if size else data
        entries = []
        for i in range(len(data) // 32):
            raw = data[i * 32:(i + 1) * 32]
            if raw[0] == 0:
                break
            if raw[0] == 0xE5 or raw[11] == ATTR_LFN:
                continue
            if raw[11] == ATTR_VOLUME_ID or raw[11] == (ATTR_VOLUME_ID | 0x20):
                continue
            if not is_root and raw[0] in (ord("."), 0x00):
                continue
            if raw[0:8].rstrip(b" ") in (b".", b".."):
                continue
            entries.append(raw)
        return entries

    def _read_tree(self):
        root = {"type": "dir", "name8": b"", "ext3": b"", "attr": ATTR_DIRECTORY,
                "time": 0, "date": 0, "children": []}
        root["children"] = self._children_of(None, 0, True, 0)
        return root

    def _children_of(self, cluster, size, is_root, parent_cluster):
        rows = self._read_dir(cluster, is_root=is_root, size=size)
        children = []
        for raw in rows:
            name8 = raw[0:8]
            ext3 = raw[8:11]
            attr = raw[11]
            c = struct.unpack_from("<H", raw, 26)[0]
            sz = struct.unpack_from("<I", raw, 28)[0]
            tm = struct.unpack_from("<H", raw, 22)[0]
            dt = struct.unpack_from("<H", raw, 24)[0]
            node = {"type": "dir" if attr & ATTR_DIRECTORY else "file",
                    "name8": name8, "ext3": ext3, "attr": attr,
                    "time": tm, "date": dt, "cluster": c, "size": sz,
                    "children": [], "data": b""}
            if node["type"] == "dir":
                if c >= 2:
                    node["children"] = self._children_of(c, sz, False, c)
            else:
                chain = self._chain(c)
                content = b"".join(self.read_cluster_bytes(cc, 1) for cc in chain)
                node["data"] = content[:sz]
            children.append(node)
        return children

    def close(self):
        self._mm.close()
        self._f.close()


def _iter_nodes(node):
    for ch in node["children"]:
        yield ch
        if ch["type"] == "dir":
            yield from _iter_nodes(ch)


def plan_geometry(total_sectors):
    """Choose FAT16 geometry for the given total sector count; returns a dict or dies."""
    root_sectors = (ROOT_ENTRIES * 32 + SECTOR - 1) // SECTOR
    chosen = None
    for spc in (8, 4, 16, 32, 64):
        fat_secs = 1
        for _ in range(8):
            data_secs = (total_sectors - RESERVED_SECTORS
                         - NUM_FATS * fat_secs - root_sectors)
            if data_secs <= 0:
                break
            clusters = data_secs // spc
            need = ((clusters + 2) * 2 + SECTOR - 1) // SECTOR
            if need == fat_secs:
                break
            fat_secs = need
        data_secs = (total_sectors - RESERVED_SECTORS
                     - NUM_FATS * fat_secs - root_sectors)
        if data_secs <= 0:
            continue
        clusters = data_secs // spc
        if clusters + 2 > 65536:
            continue
        if clusters < 4085:
            # FAT type is derived from the cluster count; too few would be treated as FAT12, skip
            continue
        chosen = {
            "spc": spc, "cluster_size": spc * SECTOR,
            "root_sectors": root_sectors, "fat_sectors": fat_secs,
            "clusters": clusters, "max_cluster": clusters + 2,
            "data_sectors": data_secs, "total_sectors": total_sectors,
            "fat_offset": RESERVED_SECTORS * SECTOR,
            "root_offset": (RESERVED_SECTORS + NUM_FATS * fat_secs) * SECTOR,
            "data_offset": (RESERVED_SECTORS + NUM_FATS * fat_secs
                            + root_sectors) * SECTOR,
        }
        break
    if chosen is None:
        die("Cannot fit FAT16 geometry for the target size (size too small or too large)")
    return chosen


class Rebuilder:
    def __init__(self, tpl, geom):
        self.tpl = tpl
        self.g = geom
        self.cs = geom["cluster_size"]
        self.fat = [0] * geom["max_cluster"]
        self.fat[0] = 0xFF00 | MEDIA_DESC
        self.fat[1] = 0xFFFF
        self.next_free = 2

    def _alloc(self, count):
        if count <= 0:
            return 0
        if self.next_free + count > self.g["max_cluster"]:
            die(f"Target image has insufficient space (need {count} more clusters)")
        start = self.next_free
        for i in range(count):
            self.fat[start + i] = start + i + 1
        self.fat[start + count - 1] = FAT16_EOC
        self.next_free += count
        return start

    def assign(self):
        """DFS pre-allocation: a directory takes its own clusters first, then its children."""
        for ch in self.tpl.root["children"]:
            self._assign_node(ch)

    def _assign_node(self, node, parent_cluster=0):
        node["parent_cluster"] = parent_cluster
        if node["type"] == "dir":
            n = max(1, ((len(node["children"]) + 2) * 32 + self.cs - 1) // self.cs)
            node["cstart"] = self._alloc(n)
            for ch in node["children"]:
                self._assign_node(ch, node["cstart"])
        else:
            node["cstart"] = self._alloc((node["size"] + self.cs - 1) // self.cs)

    def _entry(self, name8, ext3, attr, cluster, size, tm, dt):
        e = bytearray(32)
        e[0:8] = name8[:8].ljust(8, b" ")
        e[8:11] = ext3[:3].ljust(3, b" ")
        e[11] = attr
        struct.pack_into("<H", e, 22, tm)
        struct.pack_into("<H", e, 24, dt)
        struct.pack_into("<H", e, 26, cluster & 0xFFFF)
        struct.pack_into("<I", e, 28, size & 0xFFFFFFFF)
        return bytes(e)

    def _dir_bytes(self, node, parent_cluster):
        out = bytearray()
        if node is not None:
            out += self._entry(b".", b"", ATTR_DIRECTORY, node["cstart"], 0,
                               node["time"], node["date"])
            out += self._entry(b"..", b"", ATTR_DIRECTORY, parent_cluster, 0,
                               node["time"], node["date"])
            children = node["children"]
        else:
            children = self.tpl.root["children"]
        for ch in children:
            out += self._entry(ch["name8"], ch["ext3"], ch["attr"],
                               ch.get("cstart", 0),
                               0 if ch["type"] == "dir" else ch["size"],
                               ch["time"], ch["date"])
        return bytes(out)

    def write(self, out_path):
        g = self.g
        tpl = self.tpl
        zeros = b"\x00" * (1024 * 1024)

        def pad(f, target):
            pos = f.tell()
            while pos < target:
                n = min(len(zeros), target - pos)
                f.write(zeros[:n])
                pos += n

        with open(out_path, "wb") as f:
            # ---- 1. HDI header (copy the template, rewrite capacity/cylinders) ----
            hdr = bytearray(tpl._read(0, HDR_SIZE))
            struct.pack_into("<I", hdr, 0x0C, g["disk_sectors"] * SECTOR)
            struct.pack_into("<I", hdr, 0x1C, g["disk_sectors"] // SECTOR_PER_CYL)
            f.write(hdr)

            # ---- 2. IPL (sector 0) + partition table (sector 1, rewrite end CHS) + area reserved before the partition ----
            sec1 = bytearray(tpl._sector(1))
            # PC-98 partition entry: byte12 = end sector - 1, byte13 = end head, 14..15 = end cylinder
            last = g["disk_sectors"] - 1
            cyl = last // SECTOR_PER_CYL
            rem = last % SECTOR_PER_CYL
            sec1[12] = rem % SPT
            sec1[13] = rem // SPT
            struct.pack_into("<H", sec1, 14, cyl)
            f.write(tpl._sector(0))
            f.write(sec1)
            f.write(tpl._read(HDR_SIZE + 2 * SECTOR, tpl.part_offset - 2 * SECTOR))
            assert f.tell() == HDR_SIZE + tpl.part_offset

            # ---- 3. Partition boot sector (copy the template, rewrite BPB) ----
            vbr = bytearray(tpl.vbr)
            struct.pack_into("<H", vbr, 0x0B, SECTOR)
            vbr[0x0D] = g["spc"]
            struct.pack_into("<H", vbr, 0x0E, RESERVED_SECTORS)
            vbr[0x10] = NUM_FATS
            struct.pack_into("<H", vbr, 0x11, ROOT_ENTRIES)
            total = g["total_sectors"]
            struct.pack_into("<H", vbr, 0x13, total if total <= 0xFFFF else 0)
            vbr[0x15] = MEDIA_DESC
            struct.pack_into("<H", vbr, 0x16, g["fat_sectors"])
            struct.pack_into("<H", vbr, 0x18, SPT)
            struct.pack_into("<H", vbr, 0x1A, HEADS)
            struct.pack_into("<I", vbr, 0x1C, g["part_lba"])
            struct.pack_into("<I", vbr, 0x20, total)

            # The FreeDOS(98) boot sector has the start LBAs of the FAT / root
            # directory / data area embedded as constants (template layout: FAT=2,
            # root=502, root directory 192 sectors, data=694). Rewrite them only
            # when they match the values derived from the template BPB; after
            # changing the size they must be kept in sync, otherwise the boot
            # sector still searches for the root directory at the template layout
            # and prints "FreeDOS(98) Err!".
            tpl_root_lba = tpl.reserved + tpl.num_fats * tpl.fat_sectors
            tpl_data_lba = tpl_root_lba + tpl.root_sectors
            if (struct.unpack_from("<H", vbr, 0x45)[0] == tpl.reserved
                    and struct.unpack_from("<I", vbr, 0x47)[0] == tpl_root_lba
                    and struct.unpack_from("<H", vbr, 0x4B)[0] == tpl.root_sectors
                    and struct.unpack_from("<I", vbr, 0x51)[0] == tpl_data_lba):
                root_lba = RESERVED_SECTORS + NUM_FATS * g["fat_sectors"]
                struct.pack_into("<HI", vbr, 0x45, RESERVED_SECTORS, 0)
                struct.pack_into("<HI", vbr, 0x47, root_lba, 0)
                struct.pack_into("<H", vbr, 0x4B, g["root_sectors"])
                struct.pack_into("<HI", vbr, 0x51,
                                 root_lba + g["root_sectors"], 0)
            f.write(vbr)

            # ---- 4. Reserved sectors (after template sector 2, all zeros) ----
            f.write(tpl._read(HDR_SIZE + tpl.part_offset + SECTOR,
                              (tpl.reserved - 1) * SECTOR))

            # ---- 5. Two FAT copies ----
            fat_bytes = bytearray(g["fat_sectors"] * SECTOR)
            for i, val in enumerate(self.fat):
                struct.pack_into("<H", fat_bytes, i * 2, val & 0xFFFF)
            for _ in range(NUM_FATS):
                f.write(fat_bytes)

            # ---- 6. Root directory ----
            root_bytes = self._dir_bytes(None, 0)
            if len(root_bytes) > g["root_sectors"] * SECTOR:
                die("Root directory entries overflow")
            f.write(root_bytes.ljust(g["root_sectors"] * SECTOR, b"\x00"))

            # ---- 7. Data area: DFS order matches allocation order, write sequentially ----
            for ch in tpl.root["children"]:
                self._write_node(f, ch)

            # ---- 8. Pad to the target total length ----
            f.truncate(HDR_SIZE + g["disk_sectors"] * SECTOR)

    def _write_node(self, f, node):
        cs = self.cs
        if node["type"] == "dir":
            data = self._dir_bytes(node, node["parent_cluster"])
            n = max(1, (len(data) + cs - 1) // cs)
            f.write(data.ljust(n * cs, b"\x00"))
            for ch in node["children"]:
                self._write_node(f, ch)
        else:
            n = (node["size"] + cs - 1) // cs
            if n:
                f.write(node["data"].ljust(n * cs, b"\x00"))


def verify(src, out_path):
    """Read the output back and compare the file tree with the template (name/attr/size/content hash)."""
    out = TemplateFat(out_path)
    src_root = src.root
    out_root = out.root

    def snapshot(root):
        items = {}
        for n in _iter_nodes(root):
            path = ((n["name8"].rstrip(b" ").decode("ascii", "replace") + "." +
                     n["ext3"].rstrip(b" ").decode("ascii", "replace")).rstrip("."))
            items[path] = (n["type"], n["attr"],
                           None if n["type"] == "dir" else
                           (n["size"], hashlib.sha256(n["data"]).hexdigest()))
        return items

    a = snapshot(src_root)
    b = snapshot(out_root)
    problems = []
    for k, v in a.items():
        if k not in b:
            problems.append(f"Missing: {k}")
        elif b[k] != v:
            problems.append(f"Mismatch: {k} (template {v} / output {b[k]})")
    for k in b:
        if k not in a:
            problems.append(f"Extra: {k}")
    out.close()
    return problems


def main():
    ap = argparse.ArgumentParser(
        description="Build a FreeDOS(98) base HDI of a given size without the game engine")
    ap.add_argument("--size", default="250M",
                    help="target image size, e.g. 250M / 500MB / 2G (default 250M)")
    ap.add_argument("--template", default=None, help="template HDI (defaults to the 10MB base bundled in the package)")
    ap.add_argument("--out", default=None, help="output path (default build/base_<size>_clean.hdi)")
    ap.add_argument("--force", action="store_true", help="allow overwriting an existing output file")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    tpl_path = args.template
    if not tpl_path:
        for name in ("base_freedos98_scsi_10m_clean.hdi",
                     "base_freedos98_scsi_250m_clean.hdi"):
            candidate = os.path.join(here, "tools_open", name)
            if os.path.isfile(candidate):
                tpl_path = candidate
                break
        else:
            tpl_path = os.path.join(here, "tools_open",
                                    "base_freedos98_scsi_250m_clean.hdi")
    if not os.path.isfile(tpl_path):
        die(f"Template image not found: {tpl_path}")

    want = parse_size(args.size)
    total_sectors = want // SECTOR
    total_sectors -= total_sectors % SECTOR_PER_CYL   # align to whole cylinders
    if total_sectors <= 0:
        die("Target size too small (at least one cylinder)")
    take = total_sectors * SECTOR

    tag = f"{take // (1024 * 1024)}m"
    out_path = args.out or os.path.join(here, "build",
                                        f"base_freedos98_scsi_{tag}_clean.hdi")
    if os.path.abspath(out_path) == os.path.abspath(tpl_path) and not args.force:
        die("Output path equals the template path; use another --out or add --force (will overwrite the template)")
    if os.path.exists(out_path) and not args.force:
        die(f"Output already exists: {out_path} (add --force to overwrite)")
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

    print(f"Template: {tpl_path}")
    tpl = TemplateFat(tpl_path)
    part_lba = tpl.part_offset // SECTOR
    part_sectors = total_sectors - part_lba
    if part_sectors <= 0:
        die("Target size too small (cannot hold the boot area before the partition start)")
    geom = plan_geometry(part_sectors)
    geom["disk_sectors"] = total_sectors
    geom["part_lba"] = part_lba

    # Pre-check: does the content fit?
    need_clusters = 0
    for n in _iter_nodes(tpl.root):
        if n["type"] == "dir":
            need_clusters += max(1, ((len(n["children"]) + 2) * 32
                                     + geom["cluster_size"] - 1) // geom["cluster_size"])
        else:
            need_clusters += (n["size"] + geom["cluster_size"] - 1) // geom["cluster_size"]
    if need_clusters > geom["clusters"]:
        die(f"Insufficient size: content needs {need_clusters} clusters, {geom['clusters']} available")

    print(f"Target: {take:,} bytes = {total_sectors:,} sectors "
          f"({total_sectors // SECTOR_PER_CYL} cylinders)")
    print(f"Geometry: cluster {geom['cluster_size']}B ({geom['spc']} sectors), "
          f"FAT {geom['fat_sectors']} sectors x{NUM_FATS}, "
          f"root directory {ROOT_ENTRIES} entries, {geom['clusters']} clusters total")

    rb = Rebuilder(tpl, geom)
    rb.assign()
    used = rb.next_free - 2
    rb.write(out_path)
    tpl.close()

    problems = verify(TemplateFat(tpl_path), out_path)
    print(f"Generated: {out_path}")
    print(f"  File tree verification: {'PASS' if not problems else 'FAIL'}")
    for p in problems[:20]:
        print(f"    {p}")
    print(f"  Clusters used: {used}/{geom['clusters']} ({geom['clusters'] - used} free)")
    print(f"  Image contains no game engine (template is a clean FreeDOS(98) system)")
    if problems:
        sys.exit(1)


if __name__ == "__main__":
    main()

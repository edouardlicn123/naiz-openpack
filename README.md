# naiz-openpack

**Open-source asset pack for the Naiz deployment chain.** It replaces the commercial DOS
environment with fully open-source components, so Naiz (a PC-98 DOS game engine) can build and
boot game images without closed-source MS-DOS / VEM486 / DOS4GW.

## What this project is for

When Naiz packs a game into a PC-98 hard-disk image (HDI), it needs a **clean system disk** as a
base, then injects the engine and game files into it. The commercial chain uses an MS-DOS 5.0 +
VEM486 + DOS/4GW base (closed source, shipped in
[naiz_cmpack](https://github.com/edouardlicn123/naiz_cmpack) under `tools_commercial/`).

This repository provides the **open-source counterpart**, packaged as `tools_open.zip` (it unpacks
directly into the main project's `tools_open/` directory):

- DOS system: FreeDOS(98) kernel + FreeCOM, HIMEMX for memory management (EMM386(98) as an
  alternative), CTMOUSE for the mouse;
- DOS extender: DOS/32A (BSD-style license, bound into the EXE by wlink — no external extender
  file on disk);
- Base image: a **10MB clean FreeDOS(98) HDI** (see below), with no game and no engine.

The main project's build scripts prefer `tools_open/` and fall back to `tools_commercial/` when it
is missing; `--pack openpack` selects the open-source chain. Planning documents live in the Naiz
project: `devdocs/178` (component replacement) and `devdocs/185` (dual-pipeline architecture).
Background research (FreeDOS(98) sources, extender investigation) is in
[docs/refdocs/](docs/refdocs/).

## The 10MB FreeDOS(98) base image in this pack

| Item | Details |
|---|---|
| File | `tools_open/base_freedos98_scsi_10m_clean.hdi` |
| Size | 10,448,896 bytes (`size = 9 MB`, SCSI, FAT16, 2,048-byte clusters) |
| Contents | FreeDOS(98) kernel (build 2043), COMMAND.COM, HIMEMX, CTMOUSE, FDCONFIG.SYS, etc. |
| Free space | About 5.4MB (5,007 clusters, of which the system occupies about 2,368) |
| Status | Boots straight to the `A:\>` prompt; verified on np21kai |

- Game injection **copies this base and rewrites the FAT/directory**, so the output HDI always
  matches the base size — there is no resize step;
- The size is already at the lower bound: below 8MB the cluster count drops into the FAT12
  interpretation range, so **10MB is the smallest image that still boots**;
- It also serves as the template for `make_base_hdi.py`, which can generate larger bases
  (250MB / 500MB / 2GB);
- The 250MB variant is not distributed with the repo (too large for GitHub); generate it with the
  script if you need it;
- A fresh clone can use this image as-is (it is tracked in git; large images remain ignored).

## BIOS and CGROM firmware (included)

"Open source" refers to the **software layer** (DOS, memory manager, mouse driver, extender), not
to the machine firmware. FreeDOS(98) is still an operating system running on PC-98 hardware, so the
BIOS ROM and the character generator ROM (CGROM) are required as well.

The PC-9821 ROM set is shipped in `tools_open/pc9821bios/`:

| File | Size | Role |
|---|---|---|
| `BIOS.ROM` | 98,304 B | IPL, self-test and BIOS services — **required to boot** |
| `FONT.ROM` | 288,768 B | CGROM character glyphs (JIS) — **required for text rendering** |
| `ITF.ROM` | 32,768 B | Extra firmware used by certain PC-9821 configurations |
| `SOUND.ROM` | 16,384 B | Sound-board firmware |
| `bios9821.rom` | 98,304 B | Alternate PC-9821 BIOS dump (kept for reference; np21kai uses `BIOS.ROM`) |

Verified on np21kai: with only `BIOS.ROM` + `FONT.ROM` present, the 10MB base boots to the `A:\>`
prompt and displays Japanese text; `ITF.ROM` / `SOUND.ROM` are not needed for booting (the emulator
bundle itself contains no ROM images, so these copies are the only source).

The emulator looks for `bios.rom` / `font.rom` in `~/.config/wxnp21kai/`; copy them from
`tools_open/pc9821bios/` or let the Naiz test harness do it.

**Licensing:** these ROM images are NEC copyrighted firmware and are not open source. They are
included here for convenience only; redistribution may be restricted in your jurisdiction. If you
publish this pack, you are responsible for the implications, and users who prefer to avoid it can
supply their own dumps instead.

## Packaging and release

```bash
./make_openpack.sh          # writes <repo>/tools_open.zip and prints its SHA256
```

### Generating a clean base image of a given size (no game engine)

```bash
./make_base_hdi.py --size 10M --out tools_open/base_freedos98_scsi_10m_clean.hdi --force
./make_base_hdi.py --size 250M                      # writes build/base_..._250m_clean.hdi
./make_base_hdi.py --size 500M --out build/base_500m.hdi
./make_base_hdi.py --size 2G   --out build/base_2g.hdi --force
```

- Size syntax: `250M` / `500MB` / `2G` (base 1024), rounded down to whole cylinders.
- The script only needs the Python 3 standard library. It reads the full file tree from the base
  template inside the pack and rebuilds it, with no dependency on the Naiz project (the 10MB base
  is used as the template; its file tree matches the 250MB variant).
- Cluster size adapts to the target size (2/4/8/16/32/64 sectors) and always stays within the
  FAT16 range (about 10MB – 2GB).
- The output is a **clean FreeDOS(98) system** with no game engine, ready to replace the base
  image in `tools_open/`.
- The Naiz project picks the base by the fixed file name
  `tools_open/base_freedos98_scsi_10m_clean.hdi` (`OPEN_BASE_HDI` in `tools/naiz_lib`).
  To use a larger base, override it with an environment variable, e.g.
  `NAIZ_OPEN_BASE=/path/to/base_250m_clean.hdi`.

## Using it from the Naiz project

```bash
./start.sh openpack                        # download tools_open.zip -> SHA256 check -> unpack to tools_open/
./makegame.sh build <game> --pack openpack # build data + deploy the open-source runtime (HIMEMX/CTMOUSE)
./makegame.sh make  <game> --pack openpack # inject the open-source base (10MB by default, no resize)
./makegame.sh test  <game> --pack openpack # boot with np21kai
./makegame.sh pack openpack                # write .naiz_pack so later commands default to the open-source chain
```

`--pack cmpack` switches back to the commercial chain (tools_commercial + DOS/4GW) at any time.
The two chains are mutually exclusive in deployment/injection: switching cleans up any drivers and
engines left behind by the other chain.

Then:

1. Go to https://github.com/edouardlicn123/naiz-openpack/releases/new and create a Release;
2. Upload `tools_open.zip` and record its SHA256 in the release notes;
3. Put the download URL and SHA256 into the open-source download list in the Naiz project's
   `start.sh`.

## Package contents

| Directory | Contents |
|---|---|
| `tools_open/dos_system/` | Open-source DOS chain files: FreeDOS(98) kernel, FreeCOM, FDXMS/HIMEMX, EMM386(98), CTMOUSE, MEM, SYS, etc. |
| `tools_open/licenses/` | Full license text for every component + source mapping (`SOURCES.md`) |
| `tools_open/base_freedos98_scsi_10m_clean.hdi` | Default open-source base image (10MB, FAT16, SCSI; FreeDOS(98) kernel + HIMEMX + CTMOUSE, no closed-source components; about 5.4MB free) |

## Upstream and related projects

### DOS kernel and shell

- **lpproj/fdkernel** (`nec98test` branch) — FreeDOS development kernel with tori's PC-98 work
  merged in; the kernel source for this pack.
  https://github.com/lpproj/fdkernel · Releases: https://github.com/lpproj/fdkernel/releases
- **lpproj/freecom_dbcs2** — FreeCOM DBCS Japanese edition (a COMMAND.COM replacement).
  https://github.com/lpproj/freecom_dbcs2 · Releases: https://github.com/lpproj/freecom_dbcs2/releases
- **tori's original FreeDOS(98)** — the PC-98-specific ancestor (kernel 2028/2035a, fdxms,
  emm386). http://retropc.net/tori/freedos/
- **lpproj download index** (all direct links and mirrors):
  https://bauxite.sakura.ne.jp/software/dos/freedos.htm

### Memory management (XMS / EMS / VCPI)

- **lpproj/himemx.nec** — PC-98 port of HimemX (XMS).
  https://github.com/lpproj/himemx.nec
- **lpproj/emm386.nec** — EMM386(98) v2.26 experimental build (EMS/VCPI alternative).
  https://github.com/lpproj/emm386.nec · Notes: https://github.com/lpproj/emm386.nec/blob/master/doc/emm386/NEC98.txt
- **tori emm386 (2005/2/23)** — the source of `EMM386.EXE` in this pack.
  http://retropc.net/tori/freedos/
- **JEMM386 / JEMMEx** (IBM PC design, for reference only):
  https://github.com/Baron-von-Riedesel/Jemm
- **VEM486** (the current PC-98 solution; closed-source freeware, not included here): by Koji
  Ogino, distributed on Vector.

### DOS extenders

- **DOS/32A** (BSD-style license, sources public since 2002) — **the extender used by Naiz's
  open-source chain**. Open Watcom ships it under `contrib/extender/dos32a` (sources plus
  `dos32a.exe`/`stub32a.exe`) and wlink supports `-l=dos32a` directly; the extender is embedded
  into the EXE, so no external file is needed on disk. Full license text:
  `tools_open/licenses/dos32a/LICENSE.TXT` (end-user documentation must state
  "This product uses DOS/32 Advanced DOS Extender technology.").
- **CauseWay** (public domain, released by Michael Devore in 2000) — alternative extender; its
  PM→RM reflection failed at runtime on np21kai (see Naiz project refdoc I03), so it is not used
  for now. Source mirrors: https://github.com/stsp/causeway (v3.60, from the Open Watcom tree),
  https://github.com/Baron-von-Riedesel/CauseWay · https://github.com/amindlost/cw
- **Open Watcom v2** (compiler, with built-in CauseWay link support `-l=causeway`):
  https://github.com/open-watcom/open-watcom-v2

### Mouse drivers and tools

- **CuteMouse (CTMOUSE)** — the official FreeDOS mouse driver, GPL v2.
  Source: https://github.com/FDOS/mouse · SourceForge: https://sourceforge.net/projects/cutemouse/
- **lpproj/mem.nec** — MEM 1.11p1, PC-98/IBM compatible.
  https://github.com/lpproj/mem.nec
- **FreeDOS distribution mirror** (source of `ctmouse.zip`): https://ftp.icm.edu.pl/pub/dos/freedos/

### Test environment

- **Neko Project 21/W (NP21/W)** — PC-98 emulator.
  Download: https://simk98.github.io/np21w/download.html · FreeDOS(98) guide: https://simk98.github.io/np21w/freedos98.html

### Related repositories

- **Naiz main project / commercial asset pack**: https://github.com/edouardlicn123/naiz_cmpack

## License

- Full license texts for each component are in `tools_open/licenses/`; per-file sources are listed
  in `tools_open/licenses/SOURCES.md`;
- The repository's own structural files (scripts/documentation) follow the repository LICENSE.

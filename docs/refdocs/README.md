# Reference documents

Copied from the Naiz main project (`docs/refdocs/`) on 2026-11-02. They cover the FreeDOS(98)
base ecosystem, the disk/memory environment the base image lives in, and the DOS-extender
investigation this pack is based on.

## FreeDOS(98) ecosystem

| File | Content |
|---|---|
| `I01_freedos98_base_sources.md` | Upstream sources, image layout, component-by-component evaluation, SYS.COM/kernel config mechanism |
| `I02_cwtest追凶行动计划-udspy2与kernel诊断构建.md` | Investigation plan: udspy2 exit-trace and a diagnostic fdkernel build |
| `I03_CWTEST追凶经验总结-模拟器能力边界与后续方针.md` | Investigation summary (devdocs 187–191): emulator limits, CauseWay vs DOS/32A |
| `raw/fdkernel_nec98_history.txt` | fdkernel (nec98test) change history — basis for choosing/upgrading `KERNEL.SYS` |
| `raw/nec98int.txt` | FreeDOS(98) support matrix for PC-98-specific interrupts |
| `raw/sys_fd98.txt` | SYS.COM usage and kernel built-in CONFIG options (Shift-JIS) |
| `raw/emm386_NEC98.txt` | EMM386(98) README, including its UMB caveats (Shift-JIS) |
| `raw/bauxite_freedos.htm` | Full snapshot of the lpproj distribution page |

## Disk, memory and display environment

| File | Content | Why it matters here |
|---|---|---|
| `E01_boot_disk.md` | PC-98 IPL, partition table, BPB, FAT | Directly describes the structures `make_base_hdi.py` rebuilds |
| `B01_memory_map.md` | PC-98 memory map | Layout of conventional/upper/EMS space used by HIMEMX/EMM386 |
| `B03_memory_switches.md` | PC-98 memory switches | Determines available RAM/EMS in the emulator configuration |
| `D02_kanji_display.md` | Kanji display on PC-9800 | Explains the CGROM (`FONT.ROM`) and `KWC*.SYS` dependency |

## Extender and toolchain

| File | Content | Why it matters here |
|---|---|---|
| `G08_dos4gw_interrupt_and_pit.md` | Protected-mode interrupt hooking and PIT reprogramming under DOS/4GW | Reference for DOS/32A behaviour differences |
| `G07_djgpp_pc98_toolchain.md` | DJGPP on PC-98/NP2kai | Alternative toolchain, background for rebuilding from source |

## Background (general PC-98 hardware)

| File | Content |
|---|---|
| `A01_architecture.md` | PC-98 hardware architecture overview |
| `B02_io_ports.md` | PC-98 I/O port reference |
| `G01_pc98dos_hwprogramming.md` | PC-98 DOS hardware programming guide |
| `G02_quickguide_hardware.md` | NEC PC-9800 hardware quick guide |
| `G06_bauxite_wiki.md` | bauxite PC-98x1 technical wiki digest |
| `H02_pdf_bios_techdata.md` | PC-9800 Technical Data Book — BIOS volume (digest) |

Links inside these files point to the Naiz project (`devdocs/178`, `devdocs/185`, `devdocs/187`–`191`)
and are intentionally kept as-is; those documents are not part of this repository.

# tools_open —— Naiz 开源部署链资源目录

本目录是 Naiz 主项目 `tools_open/` 的母版，由 `make_openpack.sh` 打成 `tools_open.zip` 发布。
目录结构与主项目 `tools_commercial/` 一一对应：

```
tools_open/
├── dos_system/            ← 对应 tools_commercial/dos_system/（开源 DOS 链文件）
├── pc9821bios/            ← PC-9821 的 BIOS/CGROM ROM（版权归 NEC，见注意事项）
├── licenses/              ← 每个组件的许可全文与来源对照（SOURCES.md）
└── base_freedos98_scsi_10m_clean.hdi   ← 开源基座镜像（10MB），对应
                                            tools_commercial/base_msdos5_scsi_48m_clean.hdi
```

## 在 Naiz 主项目中的使用方式

- 主项目构建脚本**自动选择**：优先 `tools_open/`，缺失时回退 `tools_commercial/`
- 解压位置：Naiz 项目根目录（zip 内已带 `tools_open/` 顶层目录）
- 也可通过 `start.sh` 的开源资源下载入口获取（见 naiz-openpack Releases）

## 文件清单

见 [licenses/SOURCES.md](licenses/SOURCES.md)（逐文件来源、版本、许可、上游链接）。

## 注意事项

- 除 `pc9821bios/` 中的 NEC 固件 ROM 外，本包内容均为可再分的开源/自由软件；闭源组件（MS-DOS、VEM486、DOS4GW）不在包内
- `pc9821bios/` 提供 `BIOS.ROM`、`FONT.ROM`（启动与显示必需，已实测仅此两份即可启动）以及可选的 `ITF.ROM`、`SOUND.ROM`；这些 ROM 版权归 NEC，仅供本地使用，公开发布需自行承担版权责任
- `dos_system/` 内含两套内核：`KERNEL.SYS`（lpproj 合并版，默认）与 `KERNEL35A.SYS`（tori 2035a，对照测试用）；两套 XMS：`FDXMS.SYS`（tori）与 `HIMEMX.EXE`（lpproj）——基座镜像 CONFIG.SYS 按测试结论选择
- `CTMOUSE.COM` 上游文件名为 `CTMOUSE.EXE`，改名为 .COM 不影响执行（DOS 按 MZ 头判别格式）

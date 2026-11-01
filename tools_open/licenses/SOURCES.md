# tools_open 资源来源对照表（SOURCES / PROVENANCE）

每个二进制文件的上游来源、版本与许可。许可全文见各同名子目录。

| 包内文件 | 上游项目与版本 | 提取位置 | 许可 | 上游地址 |
|---|---|---|---|---|
| `dos_system/KERNEL.SYS` | lpproj/fdkernel `test-20220120-cherrypick`（FreeDOS(98) DBCS 内核，FAT16） | `fdkernel_dbcs-20220120-bin.zip::nec98/kernel.sys` | GPL v2（`fdkernel/copying`） | https://github.com/lpproj/fdkernel/releases |
| `dos_system/KWC8632.SYS` | 同上（FAT32 内核备选） | 同上 `nec98/KWC8632.sys` | GPL v2 | 同上 |
| `dos_system/KERNEL35A.SYS` | tori kernel 2035a（2005/7/25，对照测试用备选内核） | `kernel_2035a_20050725.zip::kernel/bin/KERNEL.SYS` | GPL v2（FreeDOS kernel） | http://retropc.net/tori/freedos/ |
| `dos_system/COMMAND.COM` | lpproj/freecom_dbcs2 `dbcswip-20220117`（FreeCOM DBCS 日语版，PC-98） | `freecom_dbcswip-20220117-bin.zip::nec98/japanese/command.com` | GPL（`freecom/license`） | https://github.com/lpproj/freecom_dbcs2/releases |
| `dos_system/COUNTRY.SYS` | lpproj/fdkernel 同上包 | `fdkernel_dbcs-20220120-bin.zip::nec98/country.sys` | GPL v2 | https://github.com/lpproj/fdkernel/releases |
| `dos_system/SYS.COM` | lpproj/fdkernel 同上包（PC-98 传送系统用） | 同上 `nec98/sys.com` | GPL v2 | 同上 |
| `dos_system/FDXMS.SYS` | tori fdxms（2004/9/10） | `fdxms_20040910.zip::fdxms/bin/fdxms.sys` | 见 `fdxms-tori/license.txt` | http://retropc.net/tori/freedos/ |
| `dos_system/HIMEMX.EXE` | lpproj/himemx.nec v3.34（PC-98 移植版，2016/9/13） | `himemx334_nec98_20160913.zip::nec98/himemx.exe` | GPL（`himemx-nec98/LICENSE.txt`） | https://github.com/lpproj/himemx.nec/releases |
| `dos_system/EMM386.EXE` | tori emm386（2005/2/23，PC-98 专属） | `emm386_20050223.zip::emm386/BIN/EMM386.EXE` | 见 `emm386-tori/LICENSE.TXT` | http://retropc.net/tori/freedos/ |
| `dos_system/MEM.EXE` | lpproj/mem.nec 1.11p1（PC98/IBM 兼用，2018/11/13） | `mem11p1-20181113.zip::bin/mem.exe` | GPL（`mem-nec98/license.txt`） | https://github.com/lpproj/mem.nec/releases |
| `dos_system/CTMOUSE.COM` | CuteMouse 2.1b4（FreeDOS 1.4 仓库包） | `ctmouse.zip::BIN/CTMOUSE.EXE` **改名为 .COM**（DOS 按文件头 MZ 判别格式，与扩展名无关） | GPL v2（`ctmouse/COPYING-GPLv2`） | https://github.com/FDOS/mouse ・ https://sourceforge.net/projects/cutemouse/ |
| `pc9821bios/BIOS.ROM` | PC-9821 BIOS ROM（96KB，来源 naiz_cmpack 的 `tools_commercial/pc9821bios/`） | `pc9821bios/BIOS.ROM` | NEC 版权固件，非开源；仅供本地使用 | — |
| `pc9821bios/FONT.ROM` | PC-98 CGROM（汉字字形，288KB） | `pc9821bios/FONT.ROM` | NEC 版权固件，非开源 | — |
| `pc9821bios/ITF.ROM` | PC-9821 附加固件（32KB，非启动必需） | `pc9821bios/ITF.ROM` | NEC 版权固件 | — |
| `pc9821bios/SOUND.ROM` | 声卡固件（16KB） | `pc9821bios/SOUND.ROM` | NEC 版权固件 | — |
| `pc9821bios/bios9821.rom` | PC-9821 BIOS 备用 dump（96KB，模拟器默认不用） | `pc9821bios/bios9821.rom` | NEC 版权固件 | — |
| `licenses/dos32a/LICENSE.TXT` | DOS/32 Advanced DOS Extender（Narech K.，Open Watcom contrib `extender/dos32a`，v9.12） | `contrib/extender/dos32a/license.txt` | BSD 式许可（要求保留版权声明；终端文档需注明 "This product uses DOS/32 Advanced DOS Extender technology."） | https://github.com/open-watcom/open-watcom-v2 |

## 下载源镜像备注

- lpproj 系 zip 均来自 GitHub Releases（上述仓库），bauxite 导航页：https://bauxite.sakura.ne.jp/software/dos/freedos.htm
- tori 系 zip 来自 tori 原站：http://retropc.net/tori/freedos/
- `ctmouse.zip` 来自 FreeDOS 仓库镜像：https://ftp.icm.edu.pl/pub/dos/freedos/repositories/1.4/base/ctmouse.zip（ibiblio 原站：https://www.ibiblio.org/pub/micro/pc-stuff/freedos/）

## 不在本包内的组件（闭源，走 naiz_cmpack / tools_commercial）

- MS-DOS 5.0 (NEC) 基座镜像与 IO.SYS/MSDOS.SYS
- VEM486.EXE 内存管理器（荻野晃史，免费但闭源）
- DOS4GW.EXE（Tenberry，商业）
（`pc9821bios/` 的 ROM 虽非开源，但为方便开箱即用已随包分发，见上表）

开源基座镜像 `base_freedos98_scsi_48m_clean.hdi` 制作完成（Naiz 主项目 devdoc 185 阶段 O2）后将放入 `tools_open/` 根目录，与 `tools_commercial/base_msdos5_scsi_48m_clean.hdi` 对应。

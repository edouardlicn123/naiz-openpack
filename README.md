# naiz-openpack

Naiz（PC-98 DOS 游戏引擎）部署链**开源资源包**仓库。提供 `tools_open.zip`，对应主项目的
`tools_open/` 目录，与商业资源包 [naiz_cmpack](https://github.com/edouardlicn123/naiz_cmpack)
（`tools_commercial/`）并存：主项目构建脚本优先使用 `tools_open/`，缺失时回退 `tools_commercial/`。

规划文档见 Naiz 主项目 `devdocs/178`（组件替换）与 `devdocs/185`（双管线架构）。

## 打包与发布流程

```bash
./make_openpack.sh          # 产出 ~/tools_open.zip 并打印 SHA256
```

然后：

1. 到 https://github.com/edouardlicn123/naiz-openpack/releases/new 新建 Release
2. 上传 `tools_open.zip`，并在说明中记录 SHA256
3. 把下载 URL 与 SHA256 写入 Naiz 主项目 `start.sh` 的开源资源下载清单

## 包内容

| 目录 | 内容 |
|---|---|
| `tools_open/dos_system/` | FreeDOS(98) 内核、FreeCOM、FDXMS/HIMEMX、EMM386(98)、CTMOUSE、MEM、SYS 等开源 DOS 链文件 |
| `tools_open/licenses/` | 每个组件的许可全文 + 来源对照表（SOURCES.md） |
| `tools_open/base_freedos98_scsi_48m_clean.hdi` | （规划中）开源基座镜像，48MB/FAT16/SCSI，与商业基座同规格 |

## 跨项目链接（上游与相关项目）

### DOS 内核与 shell

- **lpproj/fdkernel**（nec98test 分支）——FreeDOS 开发内核 + tori PC-98 成果合并版，本包内核来源
  https://github.com/lpproj/fdkernel ・ Releases: https://github.com/lpproj/fdkernel/releases
- **lpproj/freecom_dbcs2**——FreeCOM DBCS 日语版（COMMAND.COM 替代）
  https://github.com/lpproj/freecom_dbcs2 ・ Releases: https://github.com/lpproj/freecom_dbcs2/releases
- **tori 原始 FreeDOS(98)**——PC-98 特化元祖（kernel 2028/2035a、fdxms、emm386）
  http://retropc.net/tori/freedos/
- **lpproj 下载导航页**（含全部直链与镜像）：https://bauxite.sakura.ne.jp/software/dos/freedos.htm

### 内存管理（XMS / EMS / VCPI）

- **lpproj/himemx.nec**——HimemX PC-98 移植版（XMS）
  https://github.com/lpproj/himemx.nec
- **lpproj/emm386.nec**——EMM386(98) v2.26 試作（EMS/VCPI 备选）
  https://github.com/lpproj/emm386.nec ・ 说明: https://github.com/lpproj/emm386.nec/blob/master/doc/emm386/NEC98.txt
- **tori emm386（2005/2/23）**——本包 EMM386.EXE 来源
  http://retropc.net/tori/freedos/
- **JEMM386 / JEMMEx**（IBM PC 设计，对照参考）
  https://github.com/Baron-von-Riedesel/Jemm
- **VEM486**（PC-98 现役方案，闭源免费，不在本包）：荻野晃史作，Vector 配布

### DOS 扩展器（extender）

- **CauseWay**（Public Domain，2000 年 Michael Devore 释放）——Naiz 开源链的 DOS/4GW 替代
  源码镜像: https://github.com/stsp/causeway （v3.60，源自 Open Watcom 源码树）
  https://github.com/Baron-von-Riedesel/CauseWay ・ https://github.com/amindlost/cw
- **Open Watcom v2**（编译器，自带 CauseWay 链接支持 `-l=causeway`）
  https://github.com/open-watcom/open-watcom-v2

### 鼠标驱动与工具

- **CuteMouse (CTMOUSE)**——FreeDOS 官方鼠标驱动，GPL v2
  源码: https://github.com/FDOS/mouse ・ SourceForge: https://sourceforge.net/projects/cutemouse/
- **lpproj/mem.nec**——MEM 1.11p1 PC98/IBM 兼用版
  https://github.com/lpproj/mem.nec
- **FreeDOS 发行仓库镜像**（ctmouse.zip 来源）：https://ftp.icm.edu.pl/pub/dos/freedos/

### 验证环境

- **Neko Project 21/W (NP21/W)**——PC-98 模拟器
  下载: https://simk98.github.io/np21w/download.html ・ FreeDOS(98) 使用教程: https://simk98.github.io/np21w/freedos98.html

### 关联仓库

- **Naiz 主项目 / 商业资源包**：https://github.com/edouardlicn123/naiz_cmpack

## 许可

- 各组件许可全文见 `tools_open/licenses/`，逐文件来源见 `tools_open/licenses/SOURCES.md`
- 本仓库自身结构文件（脚本/说明）按仓库 LICENSE 处理

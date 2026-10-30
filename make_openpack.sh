#!/bin/bash
# naiz-openpack 打包脚本
# 把 tools_open/ 打成 tools_open.zip（对应 Naiz 主项目的 tools_open/ 资源目录，
# 角色等同于 naiz_cmpack 的 tools_commercial.zip）。
#
# 用法:
#   ./make_openpack.sh                # 输出到 ~/tools_open.zip
#   ./make_openpack.sh <输出路径.zip>  # 指定输出
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
SRC="$REPO_ROOT/tools_open"
OUT="${1:-$HOME/tools_open.zip}"

if [ ! -d "$SRC/dos_system" ]; then
    echo "错误: 找不到 $SRC/dos_system，请在仓库根目录运行" >&2
    exit 1
fi
if ! command -v zip >/dev/null 2>&1; then
    echo "错误: 需要 zip 命令（sudo apt install zip）" >&2
    exit 1
fi

mkdir -p "$(dirname "$OUT")"
rm -f "$OUT"
# zip 内保留 tools_open/ 顶层目录，与 tools_commercial.zip 解压行为一致
(cd "$REPO_ROOT" && zip -r -q "$OUT" tools_open)

echo "===== 打包完成 ====="
ls -l "$OUT"
echo ""
echo "SHA256:"
sha256sum "$OUT"
echo ""
echo "后续步骤:"
echo "  1. 到 https://github.com/edouardlicn123/naiz-openpack/releases/new 上传本文件"
echo "  2. 把下载 URL 与上面的 SHA256 提供给 Naiz 主项目，写入 start.sh 下载清单"

#!/bin/bash
# naiz-openpack packaging script
# Packs tools_open/ into tools_open.zip (the tools_open/ asset directory of the
# Naiz main project; it plays the same role as tools_commercial.zip in naiz_cmpack).
#
# Usage:
#   ./make_openpack.sh                # writes to <repo>/tools_open.zip
#   ./make_openpack.sh <output.zip>   # explicit output path
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
SRC="$REPO_ROOT/tools_open"
OUT="${1:-$REPO_ROOT/tools_open.zip}"

if [ ! -d "$SRC/dos_system" ]; then
    echo "Error: $SRC/dos_system not found; run this from the repository root" >&2
    exit 1
fi
if ! command -v zip >/dev/null 2>&1; then
    echo "Error: the zip command is required (sudo apt install zip)" >&2
    exit 1
fi

mkdir -p "$(dirname "$OUT")"
rm -f "$OUT"
# Keep the top-level tools_open/ directory inside the zip, matching how
# tools_commercial.zip extracts.
# Do not ship the 250MB reference base (e.g. if regenerated locally) in the
# release package: the default base is the 10MB small image
# (tools_open/base_freedos98_scsi_10m_clean.hdi); users who need a larger
# image can generate one with make_base_hdi.py --size.
# `-X` strips extended attributes (including access time); otherwise the same
# content would get a different SHA256 on every run and could not match the
# checksum registered in start.sh.
(cd "$REPO_ROOT" && zip -r -q -X "$OUT" tools_open \
    -x tools_open/base_freedos98_scsi_250m_clean.hdi)

echo "===== Packaging complete ====="
ls -l "$OUT"
echo ""
echo "SHA256:"
sha256sum "$OUT"
echo ""
echo "Next steps:"
echo "  1. Upload this file to https://github.com/edouardlicn123/naiz-openpack/releases/new"
echo "  2. Give the download URL and the SHA256 above to the Naiz main project and add them to the start.sh download list"

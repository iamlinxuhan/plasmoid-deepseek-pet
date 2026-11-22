#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PKG="$ROOT/package"
DIST="$ROOT/dist"
OUT="$DIST/deepseek大肥鱼-FULL.plasmoid"

mkdir -p "$DIST"
rm -f "$OUT"

# 先做一次结构检查
test -f "$PKG/metadata.json"
test -f "$PKG/contents/ui/main.qml"
test -f "$PKG/contents/config/main.xml"

cd "$PKG"
zip -r -q -9 "$OUT" .

echo "已生成：$OUT"
du -h "$OUT"

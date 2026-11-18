#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/package/contents/ui/petmask"
mkdir -p "$OUT"
MOC="$(command -v moc || echo /usr/lib/qt6/libexec/moc)"
"$MOC" "$ROOT/tools/petmask/petmask.h" -o "$ROOT/tools/petmask/moc_petmask.cpp"
g++ -O2 -fPIC -shared \
  "$ROOT/tools/petmask/petmask.cpp" \
  "$ROOT/tools/petmask/moc_petmask.cpp" \
  -o "$OUT/libpetmask.so" \
  $(pkg-config --cflags --libs Qt6Qml Qt6Gui)
cat > "$OUT/qmldir" <<'QMLDIR'
module petmask
plugin petmask
classname PetMaskPlugin
QMLDIR
echo "built $OUT/libpetmask.so"

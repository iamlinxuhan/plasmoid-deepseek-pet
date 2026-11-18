#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/reference/dsh-pet-indesktop/assets/characters/shenshen/videos"
OUT="$ROOT/package/contents/ui/assets/anim"
mkdir -p "$OUT"
find "$SRC" -name '*.webm' -not -path '*/events/balance/*' -print0 |
  xargs -0 -P 6 -I{} "$ROOT/tools/convert-one.sh" "{}" "$OUT"

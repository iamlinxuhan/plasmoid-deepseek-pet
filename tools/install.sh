#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PKG="$ROOT/dist/deepseek大肥鱼-FULL.plasmoid"

if [ ! -f "$PKG" ]; then
    "$ROOT/tools/build.sh"
fi

if kpackagetool6 -t Plasma/Applet -s com.github.iamlinxuhan.deepseekpet >/dev/null 2>&1; then
    kpackagetool6 -t Plasma/Applet -u "$PKG"
else
    kpackagetool6 -t Plasma/Applet -i "$PKG"
fi

echo "安装完成。右键桌面 → 添加组件 → 搜索「DeepSeek 大肥鱼」。"

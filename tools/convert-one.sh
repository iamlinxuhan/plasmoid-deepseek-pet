#!/usr/bin/env bash
set -euo pipefail
src="$1"
outdir="$2"
name="$(basename "$src" .webm)"
case "$name" in
  余额-*) exit 0 ;;
  # 升级源改过名，本项目沿用旧素材名以保持目录/配置兼容。
  漂浮踏步) name="原地漂浮踏步" ;;
  左转奔跑) name="原地左转奔跑" ;;
esac
ffmpeg -y -v error -c:v libvpx-vp9 -i "$src" \
  -vf "fps=20,scale=384:216:flags=lanczos,format=rgba,lut=c3='if(lt(val,2),0,val)'" \
  -c:v libwebp_anim -lossless 0 -q:v 50 -loop 0 -an \
  "$outdir/$name.webp"

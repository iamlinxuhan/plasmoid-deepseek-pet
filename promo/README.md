# 大肥鱼宣传片 / 封面

- `film_pet.py` —— 4096×2560 @ 60fps、49.5 秒宣传片。画面全部 QPainter 现画，宠物帧从上游 640×360 WebM 现抽。
- `pet_music.py` —— 原创配乐：Am–F–C–G、92 BPM，含铺底、分解和弦、软底鼓、侧链、混响与一条五声音阶主旋律；按场景分段。
- `covers_pet.py` —— 六种封面构图：16:9 / 16:10 / 4:3 / 3:4 / 9:16 / 1:1，输出到 `store/covers/`。
- `timeline.py` —— 场景时间轴，配乐和视频共用。

## 渲染

需要 PyQt5、numpy、Pillow、ffmpeg；宠物帧默认从 `reference/dsh-pet-indesktop` / `reference/dsh-pet-src` 抽取，抽不到时退回包内动画 WebP。

```bash
python3 -I promo/film_pet.py --preview 1,8,16,27,35,44   # 预览静帧
python3 -I promo/film_pet.py --render                     # 4K60 + 配乐
python3 -I promo/covers_pet.py                            # 六种封面
```

产物：

- `promo/deepseek-pet-promo-4k60.mp4`
- `store/covers/deepseek-pet-cover-*.png`
- `store/bilibili-cover.png`（1146×717）
- `store/douyin-cover.png`（1080×1920）

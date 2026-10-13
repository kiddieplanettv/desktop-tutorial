---
name: render-pipeline
description: Videoyu Remotion ile render edip FFmpeg ile YouTube'a hazır hale getirir (1080p/4K, 30/60 fps, ses normalizasyonu). Önizleme veya final render, dosya boyutu ya da ses seviyesi sorunlarında kullan.
---

# Render Pipeline

## Önizleme (hızlı)
```bash
npx remotion render DancingAnimals out/preview.mp4 --scale=0.5 --frames=0-600
```

## Final
```bash
npx remotion render DancingAnimals out/video.mp4 --codec=h264 --crf=16 --audio-bitrate=320k
# 4K: --scale=2
```
- Remotion Chrome indiremezse: `REMOTION_BROWSER=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell`.
- 60 fps için `plan_timeline.py --fps 60` ile timeline'ı yeniden üret. fps'i Remotion tarafında elle değiştirme.

## Ses normalizasyonu (YouTube: -14 LUFS)
```bash
ffmpeg -i out/video.mp4 -c:v copy -af loudnorm=I=-14:TP=-1.0:LRA=11 -c:a aac -b:a 320k out/video_final.mp4
```

## Son kontroller
- `ffprobe out/video_final.mp4` ile video ve ses sürelerinin şarkı süresiyle eşleştiğini doğrula (fark < 1 kare).
- İlk ve son karenin siyah veya boş olmadığını **visual-qa** ile kontrol et.

# Render ayarları

Video çıktısı `scripts/render.mjs` ile alınır (Remotion `renderMedia`):

- Kodek: H.264 (`h264`), piksel biçimi `yuv420p`, renk alanı BT.709, CRF 18
- Çözünürlük 1920×1080 (`--scale=0.5` → 960×540 önizleme), 30 FPS
- Ses: varsayılan sessiz (`muted`), `--music` ile `timing.json`'daki şarkı eklenir
- WebGL: `--gl=angle` (GPU) veya `--gl=swangle` (GPU'suz sunucu)
- Bitince ffprobe ile doğrulama yapılır; dosya yoksa veya bozuksa hata verir.

Studio içindeki **Render** düğmesi de aynı kompozisyonları kullanır; varsayılanlar `remotion.config.ts` içindedir.

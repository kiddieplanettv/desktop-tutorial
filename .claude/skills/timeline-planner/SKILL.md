---
name: timeline-planner
description: beats.json'dan intro, ölçülere hizalı dans blokları ve outro içeren public/data/timeline.json üretir. Toplam kare sayısı şarkı süresine birebir eşittir. Video süresini, intro/outro uzunluğunu ya da hareket sırasını değiştirirken kullan.
---

# Timeline Planner

```bash
.venv/bin/python scripts/plan_timeline.py public/data/beats.json --fps 30 \
  --intro-min 4 --outro-min 6 --bars-per-block 4
```

## Kurallar
- `durationInFrames = ceil(duration * fps)`. Video ne kısa ne uzun olur. Script bunu `assert` ile doğrular.
- Intro, `intro-min` saniyeden sonraki ilk ölçü başında biter. Outro, şarkı bitmeden en az `outro-min` saniye önceki ölçü başında başlar.
- Bloklar `bars-per-block` ölçü uzunluğundadır (varsayılan 4). Bir bölüm sınırı bloğun ortasına düşerse blok orada kesilir. Böylece nakarat geçişinde hareket de değişir.
- Hareket havuzu: enerji 0.6'nın üzerindeyse `jump, spin, slideLeftRight, clapUp`, altındaysa `sway, bounce, armWave`.
- Sözlerden gelen komutlar (`left`, `right`, `jump`, `clap`...) **lyrics-sync** çıktısıyla bloğun hareketinin üzerine yazılabilir. Bunu Remotion tarafında `captions.json` okuyarak yap.

## Remotion tarafı
`src/Root.tsx` dosyasındaki `calculateMetadata`, `timeline.json`'u okuyup süreyi ve fps'i oradan alır. Kompozisyon süresini elle yazma.

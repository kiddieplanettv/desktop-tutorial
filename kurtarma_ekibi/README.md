# Kurtarma Ekibi – 6 dakikalık 3D çocuk videosu (Blender)

Şarkısız, sadece animasyon + ses efekti + hafif fon müziği içeren, tamamen kodla üretilmiş 3D çizgi film.

| Bölüm | Süre | İçerik |
|---|---|---|
| `intro` | 0:00–0:20 | Kasabaya iniş, "KURTARMA EKİBİ" başlığı, araçlar tek tek garajdan çıkıp selam veriyor |
| `ep_police` | 0:20–1:15 | Polis arabası kaybolan yavru köpeği annesine götürüyor |
| `ep_ambulance` | 1:15–2:10 | Ambulans dizini incitmiş tavşanın yarasını sarıyor |
| `ep_fire` | 2:10–3:05 | İtfaiye kamp ateşini söndürüyor, ağaçta kalan kediyi merdivenle indiriyor |
| `ep_tow` | 3:05–4:00 | Çekici bozulan arabayı tamirciye çekiyor |
| `ep_heli` | 4:00–4:55 | Helikopter dağda mahsur kalan kuzuyu annesine uçuruyor |
| `game` | 4:55–5:40 | "Bu ses kimin?" oyunu: siluet + ses → ışıklar yanınca araç ortaya çıkıyor |
| `finale` | 5:40–6:00 | Herkes birlikte kutluyor, "HOŞÇA KALIN!" |

## Üretim

Gerekenler: Blender 4.0+, Python 3 + numpy, ffmpeg, `fonts-comfortaa`.

```bash
# 1) sahneleri kur (build/<bölüm>.blend + ses olay listeleri)
for k in police ambulance fire tow; do blender -b -P seg_episode.py -- $k; done
for k in heli intro game finale; do blender -b -P seg_$k.py; done
# 2) render (EEVEE, 960x540, kaldığı yerden devam eder)
./render_seg.sh intro ep_police ep_ambulance ep_fire ep_tow ep_heli game finale
# 3) müzik + efektler
python3 audio.py
# 4) birleştir -> KurtarmaEkibi.mp4 (1280x720)
./assemble.sh
```

Dosyalar:
- `lib.py` – ortak yapı taşları: kasaba, istasyon, yüzlü araçlar, hayvanlar, efektler (konfeti, balon, kalp, su, duman, ateş), kamera yardımcıları
- `seg_*.py` – her bölümün sahnesi ve animasyonu
- `audio.py` – numpy ile sentezlenen fon müziği ve tüm ses efektleri (siren, bip bip, havlama, miyav, meee…)

# Minik Ustalar – 6 dakikalık oyuncak araç videosu (Blender)

Beş araç (araba, çekici, damperli, vinç, kamyon) Meshy'de tasarlandı; sahneler, çevre ve animasyon tamamen bu klasördeki Blender betikleriyle üretiliyor.

## Kendi bilgisayarınızda render (Windows)

1. Bu dalı indirin (GitHub'da **Code → Download ZIP**) ve klasörü açın.
2. **Blender 4.0 veya 4.1** kurun (betikler bu sürümlerde denendi; 4.2 ve sonrası denenmedi). Birleştirme için **ffmpeg** kurulu olmalı.
3. `kurtarma_ekibi/render_toy.bat` dosyasına çift tıklayın (1280×720). 1920×1080 için komut satırından `render_toy.bat --hd` yazın.
   Blender başka bir klasördeyse `.bat` dosyasının başındaki yolu düzeltin.
4. Kareler `build/<bölüm>/` klasörlerine yazılır (yarıda kesilirse kaldığı yerden devam eder); sonunda `Minik_Ustalar_6dk.mp4` hazır müzik ve efektlerle (`ses/`) oluşur.

Tek bir sahneyi Blender'da açmak için: `blender -b -P t_ep1.py` → `build/t_ep1.blend`.

Linux: `./render_toy.sh t_intro t_ep1 t_ep2 t_ep3 t_ep4 t_outro` ve `./assemble_toy.sh Minik_Ustalar_6dk.mp4 t_intro t_ep1 t_ep2 t_ep3 t_ep4 t_outro`.

Dosyalar: `t_*.py` bölümler, `t_common.py` ortak sahne, `toys.py` araç ve hareket yardımcıları, `scenery.py` çevre, `toys3d/` araç modelleri, `chk.sh` çakışma/yol denetimi.

---

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

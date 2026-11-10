# Kahraman Kasaba – Yapay Zekâ Videosu Üretim Kiti

Karakterler: kiddieplanettv'nin kendi tasarımları (`main` dalı → `karakterler/`).
Video: 6 dakika, şarkısız, konuşmasız; görüntü + ses efekti + fon müziği.
Yöntem: Karakter resimleri → (gerekirse) sahne resmi → yapay zekâ ile resimden video (Kling / PixVerse / Hailuo, ücretsiz krediler) → Claude birleştirir ve ses ekler.

## Karakter adları (istersen değiştirebilirsin)

| # | Resim dosyası | Ad | Rolü |
|---|---|---|---|
| 1 | Neşeli 3D İtfaiyeci ve Aracı.png | **İtfaiyeci Kemal** | İtfaiye eri, bıyıklı |
| 2 | Neşeli Dinozor Tişörtlü Çocuk.png | **Deniz** | Turuncu saçlı çocuk |
| 3 | Neşeli Geri Dönüşüm Kahramanı.png | **Geri Dönüşümcü Murat** | Çöp/geri dönüşüm kamyonu |
| 4 | Neşeli Parkta El Sallayan Kız.png | **Elif** | Mor puantiyeli elbiseli kız |
| 5 | Neşeli Parkta Sallanan Küçük Kız.png | **Ada** | Sarışın, tulumlu kız |
| 6 | Neşeli Çizgi Polis ve Şehir.png | **Polis Burak** | Polis memuru |
| 7 | Neşeli Çocuk Parkında El Sallayan Çocuk.png | **Emir** | Araba tişörtlü çocuk |
| 8 | Renkli Sokakta Çizgi Film Hırsızı.png | **Sinsi Sami** | Komik, zararsız hırsız |
| 9 | Renkli Sokakta Çizgi Film Koyunu.png | **Pamuk** | Koyun |
| 10 | Renkli Sokakta Çizgi Film İneği.png | **Benekli** | İnek (filigransız yeniden üretilmeli) |
| 11 | maymun.jpg | **Cimcime** | Maymun |

## 6 dakikalık akış

| Süre | Bölüm | Hikâye | Mesaj |
|---|---|---|---|
| 0:00–0:20 | Giriş | Kasaba uyanıyor, herkes kameraya el sallıyor | – |
| 0:20–1:30 | 1. Kayıp Top | Sinsi Sami çocukların topunu çalar, Polis Burak yakalar, Sami özür diler, hep birlikte oynarlar | Dürüstlük, paylaşmak |
| 1:30–2:40 | 2. Ağaçtaki Cimcime | Maymun Cimcime ağaca tırmanır inemez, İtfaiyeci Kemal merdivenle indirir | Yardımlaşma |
| 2:40–3:50 | 3. Temiz Park | Piknikten sonra park dağınık, Geri Dönüşümcü Murat çocuklarla çöpleri renkli kutulara ayırır | Doğayı korumak |
| 3:50–5:00 | 4. Kasabada Kayıp Hayvanlar | Pamuk ve Benekli çiftlikten kaçıp kasabaya gelir, çocuklar ve Polis Burak onları çiftliğe götürür | Hayvan sevgisi |
| 5:00–5:40 | 5. Ses Oyunu | Siluet + ses → "Bu kim?" (polis arabası, itfaiye, geri dönüşüm kamyonu, koyun, inek, maymun) | Sesleri tanıma |
| 5:40–6:00 | Final | Parkta büyük kutlama, konfeti, "Hoşça kalın!" | – |

## Her klipte aynı kalacak stil cümlesi (promptun sonuna ekle)

```
3D Pixar-style children's animation, soft warm studio lighting, vibrant pastel colors,
cute colorful town with cream lamp posts, round green trees, pastel shops with striped awnings,
lavender-gray road with white dashes, smooth gentle camera motion, 16:9, no text, no subtitles, no watermark
```

## Genel ipuçları

- Her klipte **o sahnedeki karakterin orijinal resmini referans/ilk kare olarak yükle**. Yüzler böyle tutarlı kalır.
- Birden çok karakter varsa önce resim aracında (karakterleri tasarladığın araç) **sahne resmi** üret: karakter resimlerini referans ver, aşağıdaki "Sahne resmi" promptunu kullan. Sonra o resmi videoya çevir.
- Klip süresi 5–10 sn. Beğenmediğin klibi yeniden üret, kredi yetiyorsa 2 versiyon alıp iyisini seç.
- Konuşma/ses gerekmez, sesi ben ekleyeceğim. Araçta ses seçeneği varsa kapatabilirsin.
- İndirdiğin dosyaları `kurtarma_ekibi/ai_video/klipler/` klasörüne `b1_k01.mp4`, `b1_k02.mp4` … diye yükle.

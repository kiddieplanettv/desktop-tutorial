# Kiddie TV — Pandi'nin Renkli Treni

2–6 yaş için 3B çocuk çizgi filmi. 1920×1080, 16:9, 30 FPS, 210 sn (6300 kare), H.264 MP4.
Teknoloji: **TypeScript + React + React Three Fiber / Three.js + Remotion**.

> **Durum: PROTOTİP (ilk 20 saniye).** Sahne 1 ve 2 gerçek 3B animasyondur.
> Sahne 3–21 zaman çizelgesinde yerini almıştır ama henüz yapılmadı; önizlemede
> açıkça **"YAPIM AŞAMASINDA — FİNAL GÖRÜNTÜ DEĞİL"** kartı gösterirler.
> Prototip onaylandıktan sonra aynı yapı üzerine diğer sahneler eklenecek.

## Kurulum ve önizleme

```bash
npm install
npm run studio        # Remotion Studio → http://localhost:3000
```

Remotion Studio'da (hepsi Studio'nun kendi çalışan kontrolleri):

| İstek | Nerede |
|---|---|
| Oynat / duraklat | Boşluk tuşu veya ▶ düğmesi |
| Baştan başlat | Oynatıcıdaki "başa dön" düğmesi |
| İleri / geri gitme | Alttaki zaman çizelgesinde tıkla/sürükle; kare kare ilerleme düğmeleri. Tüm kısayollar Studio'nun "Keyboard shortcuts" listesindedir |
| Sahne seçme | Sol listede **Sahneler/Sahne01…Sahne21**; ana videoda zaman çizelgesindeki sahne blokları (adlarıyla) |
| Aktif sahnenin başlangıç/bitişi | Sağ panelde `showGuides` açılınca görüntüde sahne adı, başlangıç → bitiş, zaman kodu, kare no |
| Tam ekran | Önizleme üstündeki tam ekran düğmesi |
| Karakter animasyonlarını kontrol | **Kontrol/PandiEylemleri** — 12 eylem tek tek (`action`), döner tabla (`turntable`), yakın plan (`kamera`) |
| Tren ve çevre kontrolü | **Kontrol/TrenTesti** — hız, kamera (yan / ön çapraz / yörünge / kabin), buhar |
| Ses dosyası alanı ve dalga formu | **Kontrol/MuzikSenkron** (aşağıya bakın) |
| Render ve ilerleme | Studio'daki **Render** düğmesi (ilerleme çubuğu gösterir) veya aşağıdaki komutlar |

Kompozisyonlar:

- `PandiTrain` — ana video (21 sahne, 210 sn). Şu an sahne 3–21 "yapım aşamasında" kartıdır.
- `Prototype20s` — ilk 20 sn (sahne 1–2), görsel kontrol için.
- `Sahneler/SahneNN` — her sahne tek başına. Yapılmamış olanların adı `-Bekliyor` ile biter.
- `Kontrol/PandiEylemleri`, `Kontrol/TrenTesti`, `Kontrol/MuzikSenkron`.

## Video çıktısı (MP4)

```bash
npm run render:prototype         # ilk 20 sn, 1920×1080
npm run render:prototype:low     # ilk 20 sn, 960×540 hızlı önizleme
npm run render:full              # 210 sn, sessiz
npm run render:full:music        # 210 sn, timing.json'daki şarkıyla
node scripts/render.mjs --comp=PandiTrain --frames=0-299   # yalnız bir aralık
node scripts/still.mjs --comp=Prototype20s --frame=0,150,450   # tek kareler (PNG)
```

- Çıktılar `out/` klasörüne yazılır. Betik, işlem bitince dosyayı **ffprobe ile doğrular**
  (kodek, çözünürlük, FPS, süre, ses akışı) ve ancak dosya gerçekten varsa "✔ MP4 oluştu" der.
  Hata olursa "✖ RENDER BAŞARISIZ" ve hata ayrıntısını yazar, çıkış kodu 1 olur.
- Format: H.264, yuv420p, BT.709, CRF 18 — YouTube'a doğrudan yüklenebilir.
- **GPU'suz** bir sunucuda `--gl=swangle` (yazılım WebGL) kullanın; GPU'lu bilgisayarda varsayılan `angle` çok daha hızlıdır.
  Referans: GPU'suz 4 çekirdekli sunucuda 1080p ≈ 3–4 sn/kare (20 sn ≈ 35 dk; 210 sn ≈ 6 saat).

## Şarkıyı sonradan ekleme (Suno MP3/WAV)

Şu an hiçbir müzik üretilmedi; video sessizdir. Şarkı geldiğinde:

1. Dosyayı `public/audio/` içine kopyalayın, ör. `public/audio/sarki.mp3`.
2. `src/timeline/timing.json` → `audio.src` alanına `"audio/sarki.mp3"` yazın
   (veya Studio'da sağ panelde `audioSrc` alanına yazıp `audioEnabled`'ı açın).
3. `startOffsetSec`: şarkının videodaki başlangıç kayması. `> 0` → şarkı geç başlar, `< 0` → şarkının başı kırpılır.
4. **Kontrol/MuzikSenkron** kompozisyonu: şarkının dalga formunu, 21 sahne bloğunu ve (BPM girilirse) vuruş ızgarasını
   aynı zaman ekseninde gösterir; oynatma başı ile birlikte dinlenebilir. Ses yoksa bunu açıkça yazar.
5. Sahne sürelerini uzatıp kısaltmak: `timing.json` içinde ilgili sahnenin `durationSec` değeri
   (veya Studio'da `sceneDurationsSec`). Başlangıç/bitişler otomatik hesaplanır, araya boş kare girmez;
   sahne içi hareketler yeni süreye orantılı esner, tren hızı ve buhar zamanları da sahneye göre oransaldır.
6. Ritim eşleştirme: şarkının `bpm` ve ilk vuruş zamanı `beatOffsetSec` girilince
   "başını ritme göre sallama" ve "dans" eylemleri bu tempoya kilitlenir. Girilmezse sakin varsayılan tempo (100) kullanılır.
   Şarkı sözleri / vokal girişleri bilinmediği için sisteme önceden eklenmedi.
7. Müzikli dışa aktarma: `npm run render:full:music`. Sessiz: `npm run render:full`.

## Proje düzeni

```
src/
  characters/   Pandi (Pandi.tsx), kafa geometrisi ve yüz dokuları (pandiHead.ts), poz modeli (pose.ts)
  train/        Ray (track.ts), tren hareketi (trainMotion.ts), ölçüler (layout.ts),
                Lokomotif, Tekerlek, Vagon, Tren, Buhar
  environments/ Gökyüzü, ışık, zemin, raylar, istasyon, ağaç/çiçek/bulut/ev/tepe, StationValley
  scenes/       Sahne01, Sahne02, ortak SceneCanvas, sahne saati, kayıt (registry.ts), bekleyen sahne kartı
  animations/   Deterministik matematik (math.ts), Pandi'nin 12 eylemi (pandiActions.ts)
  timeline/     timing.json (düzenlenebilir), çözümleyici, Studio ayar şeması, kontrol katmanı
  audio/        Sonradan eklenecek şarkı bileşeni
  assets/       reference/pandi-referans.jpg (karakter referansı), prosedürel dokular, geometri yardımcıları
  render/       Render ayarlarının açıklaması (betikler: scripts/)
  labs/         Kontrol kompozisyonları (PandiEylemleri, TrenTesti, MuzikSenkron)
scripts/        render.mjs (MP4 + doğrulama), still.mjs (PNG kareler)
```

## Teknik ilkeler

- **Kareye bağlı animasyon:** Her hareket yalnızca kare numarasından hesaplanır (`Math.random` ve gerçek saat yok;
  rastgelelik tohumlu). Aynı kare her render'da birebir aynı çıkar.
- **Sahneler bağımsız:** Her sahne kendi dosyasında ve kendi `<Sequence>`'ında. Biri değişince diğerleri etkilenmez.
- **Süreklilik:** Tren konumu bütün video için tek bir hız eğrisinin integralidir; tekerlek dönüşü = mesafe / yarıçap.
  Sahne 2'nin kamerası ve Pandi'nin pozu Sahne 1'in bittiği yerden başlar (sahne sınırında sıçrama yok —
  kare 299 ve 300 karşılaştırılarak doğrulandı).
- **Tren:** Her vagon ray üzerindeki iki boji noktasına oturur; bağlantı kolları komşu araçların gerçek uç
  noktaları arasında hesaplanır (virajlarda kopmaz, içe geçmez). Vagonlarda yazı yoktur.
- **Pandi:** Referans görsele göre kodla modellenmiş 3B karakter (dış model dosyası yok). Kafa, alt kısmı hafif
  genişleyen elipsoit; göz lekeleri, yanaklar ve tüy dokusu prosedürel; tüy kabarıklığı için "fur shell" katmanları;
  ağız ve kaşlar her karede yeniden çizilen yüz katmanıdır; gözler parlak 3B kürelerdir.
- **Işık:** Yumuşak gün ışığı + gökyüzü ışığı; yanıp sönen ışık yok, parlamalar yumuşak geçişlidir.

## Bilinen sınırlamalar (açıkça)

- Sahne 3–21 henüz yapılmadı (yalnızca etiketli bekleme kartları). Yardımcı karakterler (tavşan, fil, penguen, civciv)
  ve göl, köprü, orman, tünel, gökkuşağı ortamları bir sonraki aşamada eklenecek.
- Studio'da dosya yükleme düğmesi yok: ses dosyası `public/audio/` klasörüne kopyalanarak eklenir.
- GPU'suz ortamda render yavaştır (yukarıdaki süreler).

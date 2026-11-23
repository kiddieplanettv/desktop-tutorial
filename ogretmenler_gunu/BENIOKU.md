# Öğretmenler Günü 3D Klip – "Canım Öğretmen Kutlu Olsun"

Kiddie TV için Blender 5.2 ile hazırlanmış 1:14'lük 3D klip. Tren, renkli arabalar,
okul bahçesi ve sınıf sahnesi; sözler karaoke tarzında (söylenen kelime sarıya döner).

## Render (tek adım)

1. Bu klasörün tamamını bilgisayarınıza indirin (klasör yapısını bozmayın; `assets/` gerekli).
2. **Blender 5.2** ile `ogretmenler_gunu.blend` dosyasını açın.
   - "Otomatik Python çalıştırma" uyarısı çıkarsa izin vermenize gerek yok, sahne script kullanmaz.
3. Ekran kartını açın: *Edit → Preferences → System → Cycles Render Devices* (EEVEE otomatik ekran kartını kullanır).
4. Üstte etkin sahnenin **Montaj** olduğundan emin olun (sağ üstteki sahne seçici).
5. **Render → Render Animation** (Ctrl+F12).
6. Video şuraya yazılır: `render/Ogretmenler_Gunu_0001-2220.mp4`
   (1920×1080, 30 fps, H.264 + AAC ses, sözler gömülü).

Tahmini süre: orta seviye bir ekran kartında EEVEE ile 30–75 dakika (2220 kare).

### Yarıda kalırsa / daha hızlı isterseniz
- Önce yalnız 3D kareleri almak isterseniz: sahneyi **Sahne3D** yapın → Ctrl+F12; kareler
  `render/kareler/` klasörüne PNG olarak yazılır. Ardından **Montaj** sahnesinde scene şeridini
  bu karelerle değiştirmeniz gerekir; normalde buna gerek yoktur.
- Kaliteyi düşürüp hızlandırmak için: *Sahne3D → Render Properties → Sampling → Render* değerini
  32'den 16'ya indirin.

## Dosyalar

| Dosya | Ne işe yarar |
|---|---|
| `ogretmenler_gunu.blend` | Render alınacak sahne (Sahne3D + Montaj) |
| `build_scene.py` | Sahneyi sıfırdan kuran script (`blender -b --factory-startup -P build_scene.py`) |
| `make_karaoke.py` | Karaoke söz görsellerini üretir (`assets/karaoke/`) |
| `qa_check.py` | Hata filtresi: tüm zaman çizelgesini tarar, `qa_rapor.txt` yazar |
| `render_test.py` | Belirli kareleri hızlı test render'ı almak için |
| `assets/` | Şarkı, yazı tipi (Baloo 2, OFL lisanslı), söz ve vuruş zamanları |

## Videonun akışı

| Zaman | Söz | Görüntü |
|---|---|---|
| 0:00 | (giriş) | Tren kameraya doğru gelir, düdük buharı; okulun üstünde "Öğretmenler Günü" yazısı |
| 0:05 | Öğretmenler Günün kutlu olsun | Tren istasyona girer, arabalar sağdan gelip sıraya dizilir |
| 0:09 | Canım öğretmenim | **Sınıf**: arabalar tahtanın önünde zıplar, tahtadaki kalp atar |
| 0:13 | Kalbin her gün mutlulukla dolsun | Vagondaki kalp her kelimede biraz daha şişer, sonra gökyüzüne uçar |
| 0:21 | Sevgin bize hep bir ışık olsun | Güneş okulun arkasından doğar, "ışık" kelimesinde parlar |
| 0:29 | Her gününe binbir neşe dolsun | Balonlar, konfeti, arabalar dönerek dans eder |
| 0:37 | (ara) | Tren yakın çekim, düdük |
| 0:38 | Öğretmenler Günün kutlu olsun | Sınıfta bayrak süsler asılır, masaya hediyeler ve çiçek buketi gelir |
| 0:47 | Kalbin her gün mutlulukla dolsun | Sınıfta kalpler uçuşur |
| 0:54 | Sevgin bize hep bir ışık olsun | Okulun üstünde gökkuşağı, tren yola çıkar |
| 1:03 | Her gününe binbir neşe dolsun | Büyük kutlama: balon + konfeti |
| 1:08 | Canım öğretmenim | Tahtada **"Öğretmenler Gününüz Kutlu Olsun!"**, çiçek ve konfeti yağmuru |

Her "Canım öğretmenim!" anında aynı sınıf sahnesine dönülür (çocukların beklediği tekrar eden an);
27 çekim, ortalama 2,7 sn.

## YouTube

- Başlık: `Öğretmenler Günü Şarkısı 💐 Canım Öğretmenim | 24 Kasım | Sözleriyle Birlikte Söyle | Okul Öncesi`
- Çocuklara özel: Evet
- Videoyu bu gece yükleyip sabah 06:30'a zamanlayın (HD işleme süresi için).

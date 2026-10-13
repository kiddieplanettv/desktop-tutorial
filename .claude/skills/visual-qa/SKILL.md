---
name: visual-qa
description: Render öncesi ve sonrası görsel kalite kontrolü yapar. Belirli karelerden still alır, kontak sayfası çıkarır, beat senkronunu, karakter çakışmasını, alt yazı taşmasını ve boş kareleri denetler. Bir değişikliği teslim etmeden önce kullan.
---

# Visual QA

1. Kritik kareleri al: intro ortası, ilk blok başı, her bölüm başı, outro ve son kare.
   ```bash
   npx remotion still DancingAnimals out/qa/f0400.png --frame=400
   ```
2. Kontak sayfası (her 2 saniyede bir kare):
   ```bash
   ffmpeg -i out/preview.mp4 -vf "fps=0.5,scale=480:-1,tile=6x4" -frames:v 1 out/qa/contact.png
   ```
3. Kontrol listesi:
   - Beat karesinde karakter en vurgulu pozda mı? (`beatFrames[n]` karesini ve bir önceki kareyi karşılaştır.)
   - Karakterler birbirine veya alt yazı alanına taşıyor mu?
   - Alt yazı tek satıra sığıyor mu, okunuyor mu?
   - Blok geçişlerinde sert kesme (pop) var mı?
   - Son kare boş değil ve video şarkı bitiminde tam olarak bitiyor mu?
4. Görselleri Read aracıyla aç ve gerçekten bak. "Muhtemelen doğru" deme.

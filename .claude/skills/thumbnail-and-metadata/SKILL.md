---
name: thumbnail-and-metadata
description: YouTube kapak görseli (1280×720) ile başlık, açıklama ve etiketleri üretir. Video tamamlandığında veya kullanıcı yayın hazırlığı istediğinde kullan.
---

# Thumbnail & Metadata

## Kapak
- Kompozisyondan en enerjik kareyi seç (nakarattan, karakterlerin gözleri `happy` ve kolları yukarıdayken) ve ayrı bir `Thumbnail` kompozisyonu (1280×720) olarak kur. Videodan doğrudan ekran görüntüsü alma.
- 2-4 kelimelik büyük başlık, kalın yuvarlak font, kontur veya gölge. Karakterler büyük, yüzleri net görünsün.
- `npx remotion still Thumbnail out/thumbnail.png`

## Metin
- Başlık: şarkı adı + "| Dans Şarkısı | Çocuk Şarkıları". 60 karakteri geçmesin.
- Açıklama: ilk iki satırda şarkının ne olduğu, ardından sözler ve kanal bağlantıları.
- YouTube Kids / COPPA: videoyu "çocuklara yönelik" olarak işaretlemeyi kullanıcıya hatırlat.

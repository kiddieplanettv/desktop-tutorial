---
name: lyrics-sync
description: whisperX (gerekirse önce demucs ile vokal ayırma) ile şarkı sözlerini kelime düzeyinde zamanlar ve @remotion/captions formatında public/data/captions.json üretir. Alt yazı, karaoke vurgusu veya söz-hareket eşlemesi gerektiğinde kullan.
---

# Lyrics Sync

```bash
.venv/bin/python scripts/lyrics_sync.py public/audio/<sarki>.wav --lang en --separate
```
- `--separate`: demucs ile vokali ayırır (`public/data/stems/`). Müzik yoğun şarkılarda isabeti belirgin şekilde artırır.
- Model ağırlıkları ilk çalıştırmada **huggingface.co** (whisperX) ve **dl.fbaipublicfiles.com** (demucs) adreslerinden indirilir. Ağ bu adreslere izin vermiyorsa çalışmaz. Kullanıcıya hangi adresin engellendiğini söyle, sahte zamanlama uydurma.
- Kullanıcı söz metnini verdiyse: whisper çıktısındaki yanlış kelimeleri verilen metinle düzelt, zamanları koru.

## Gösterim
- `@remotion/captions` içindeki `createTikTokStyleCaptions` ile sözleri satırlara böl. Ekranda tek satır, alt orta, koyu yarı saydam kutu, `♪ ... ♪` biçiminde göster.
- Okunabilirlik: en az 56 px, kalın ve yuvarlak bir font (`@remotion/google-fonts`, ör. "Baloo 2" veya "Fredoka").
- Kelime vurgusu (karaoke) isteğe bağlıdır. Okul öncesi için tüm satırı sabit göstermek daha sakin olur.

---
name: audio-analyzer
description: Kullanıcının verdiği şarkıdan BPM, beat, ölçü başı (downbeat), bölüm ve enerji bilgisini çıkarır (public/data/beats.json). Yeni bir şarkı geldiğinde, beat senkronu bozuk göründüğünde ya da "şarkıyı analiz et" denildiğinde kullan.
---

# Audio Analyzer

1. Şarkıyı `public/audio/` altına koy. WAV tercih edilir, MP3 de olur. Dosya adında boşluk olmasın.
2. Çalıştır:
   ```bash
   .venv/bin/python scripts/analyze_audio.py public/audio/<sarki>.wav
   ```
   Çıktı `public/data/beats.json` dosyasına yazılır. İçinde `duration`, `bpm`, `beatsPerBar`, `beats[]`, `downbeats[]`, `barEnergy[]` (0-1 arası) ve `sectionStarts[]` bulunur.
3. Sonucu kontrol et:
   - Çocuk şarkılarında BPM genelde 90-140 arasındadır. 60 civarı çıktıysa yarım tempo, 200+ çıktıysa çift tempo yakalanmıştır. `--engine librosa` ile karşılaştır.
   - İlk downbeat 0'a yakın değilse şarkıda müziksiz bir giriş vardır. Intro bu boşluğu kapatır.
   - `sectionStarts` sayısı, kıta/nakarat yapısıyla kabaca örtüşmeli. Örtüşmüyorsa `--sections` değerini değiştir.
4. madmom varsayılan motordur ve en isabetlisidir. Hata verirse script otomatik olarak librosa'ya geçer.
5. Davul baskın değilse ve beat tespiti zayıfsa, önce demucs ile davulları ayır (`python -m demucs public/audio/x.wav`) ve analizi `drums.wav` üzerinde yap. Süre olarak her zaman orijinal dosyayı esas al.

Sonraki adım: **timeline-planner**.

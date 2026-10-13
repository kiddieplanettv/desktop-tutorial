---
name: dance-moves-library
description: Beat'e kilitli dans hareketleri kütüphanesi (sway, bounce, armWave, jump, spin, slideLeftRight, clapUp). Kare numarası ve beat listesinden karakter pozu (RigPose) üretir. Yeni hareket eklerken, hareketleri müzikle senkronlarken veya karakterler robotik göründüğünde kullan.
---

# Dance Moves Library

Hareketler `src/moves/` altında saf fonksiyonlar olarak yazılır:
```ts
(ctx: { frame: number; fps: number; beatFrames: number[]; blockStart: number; energy: number;
        characterIndex: number }) => Partial<RigPose> & { x?: number }
```

## Senkron kuralları
- Fazı beat'ten hesapla: `phase = (frame - lastBeat) / (nextBeat - lastBeat)`, değer 0..1 arası. Sabit BPM varsayma. Gerçek beat listesini kullan.
- Vuruş anı (phase = 0) hareketin **en vurgulu** pozudur: ayak yere basar, squash olur, kol en üsttedir.
- Gecikme hissi için: görsel vurguyu beat'ten 1 kare **önce** başlat (`frame + 1` ile örnekle). Göz, sesi biraz gecikmeli algılar.

## Kalite (robotik görünmemesi için)
- `spring()` ve `Easing.inOut(Easing.cubic)` kullan, doğrusal interpolasyon kullanma.
- Overlap/follow-through: kollar gövdeden 2-3 kare geç gelsin, kuyruk ve bere ponponu 4-5 kare geç gelsin.
- Squash & stretch: zıplamanın tepesinde `squash 1.08`, inişte `0.88`.
- Karakterler arasında küçük faz farkı ver: `characterIndex * 2` kare. Tamamen aynı hareket etmesinler.
- Hareket geçişleri: blok değişiminde iki pozu 6 karede karıştır, sert kesme yapma.
- Göz kırpma beat'ten bağımsız olsun: 3-5 saniyede bir, rastgele ama deterministik (`random(seed)`).

## Söz-hareket eşlemesi
`captions.json`'da "left/sola", "right/sağa", "jump/zıpla", "clap/alkış", "spin/dön" geçtiğinde, kelimenin `startMs`'inden sonraki ilk beat'ten itibaren 2 ölçü boyunca ilgili hareketi uygula.

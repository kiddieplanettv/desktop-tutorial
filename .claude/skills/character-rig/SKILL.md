---
name: character-rig
description: Hayvan karakterlerini parçalı (gövde, göz, ağız, kollar, bacaklar, aksesuar) React/SVG bileşenleri olarak kurar veya kullanıcının verdiği SVG/Rive/Spine dosyasını bağlar. Yeni karakter eklerken, karakter görünümünü değiştirirken veya kullanıcıdan karakter dosyası geldiğinde kullan.
---

# Character Rig

## Stil (referans: yuvarlak, düz renk, kalın konturlu olmayan çocuk animasyonu)
- Gövde ve baş tek bir daire ya da elips. Kollar ve bacaklar yuvarlak uçlu kalın çizgiler (`strokeLinecap="round"`).
- Gözler üç durumlu: `open`, `closed` (ˆ ˆ), `happy` (> <). Ağız: `smile`, `open`, `o`.
- Yumuşak bir yanak/çil detayı ve tek bir aksesuar (bere, fiyonk, gözlük).
- Telif: Super Simple veya başka bir markanın karakterlerini birebir kopyalama. Sadece stilden esinlen.

## Bileşen sözleşmesi
Her karakter `src/characters/<Ad>.tsx` dosyasındadır ve şu prop'ları alır:
```ts
type RigPose = {
  bodyY: number; bodyRotate: number; squash: number;   // squash: 1 = normal, <1 basık
  armL: number; armR: number;                          // derece, omuz pivotundan
  legL: number; legR: number;                          // derece, kalça pivotundan
  eyes: "open" | "closed" | "happy"; mouth: "smile" | "open" | "o";
};
```
- Her uzuv kendi `<g transform="rotate(a, pivotX, pivotY)">` grubunda dönsün. Pivotları sabit olarak tanımla.
- `squash` uygulanırken alt nokta (ayak) sabit kalmalı. Ölçeklemeyi `transform-origin` ayak hizasında yap.
- Karakter SVG'si 400×400 viewBox içinde tasarlanır. Sahnede `scale` ile boyutlandırılır.

## Kullanıcı karakter verirse
- **SVG/AI/Figma:** Katmanları yukarıdaki parçalara ayır, her katmanı ayrı `<g>` olarak al ve pivotları işaretle.
- **Rive (.riv):** `@rive-app/react-canvas` kullan. Remotion'da state machine input'larını `useCurrentFrame()` ile sür. Rive'ın kendi zamanlayıcısına güvenme, kareyi elle ilerlet.
- **Spine (.json + .atlas):** `@esotericsoftware/spine-webgl` ile kur. Animasyon zamanını `frame / fps` ile set et.
- **Tek bir resim (çizim):** Son çare `vendor/AnimatedDrawings`. Kalitesi düşüktür, kullanıcıya söyle.

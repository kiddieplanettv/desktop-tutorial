/** Hafif rüzgâr: konuma göre faz kaydırmalı, yavaş salınım (radyan). */
export const wind = (t: number, x: number, z: number, strength = 1) =>
  strength * (0.035 * Math.sin(t * 1.25 + x * 0.21 + z * 0.13) + 0.015 * Math.sin(t * 2.3 + x * 0.5));

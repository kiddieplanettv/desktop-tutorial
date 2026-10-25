// Saf, kareye bağlı (deterministik) matematik yardımcıları.
// Hiçbir fonksiyon gerçek zamanlı saat veya Math.random kullanmaz.

export const clamp = (v: number, min = 0, max = 1) => Math.min(max, Math.max(min, v));
export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
export const invLerp = (a: number, b: number, v: number) => (b === a ? 0 : (v - a) / (b - a));

export const smoothstep = (t: number) => {
  const x = clamp(t);
  return x * x * (3 - 2 * x);
};
export const smootherstep = (t: number) => {
  const x = clamp(t);
  return x * x * x * (x * (x * 6 - 15) + 10);
};
export const easeInOutSine = (t: number) => -(Math.cos(Math.PI * clamp(t)) - 1) / 2;
export const easeOutCubic = (t: number) => 1 - Math.pow(1 - clamp(t), 3);
export const easeInCubic = (t: number) => Math.pow(clamp(t), 3);
export const easeOutBack = (t: number, s = 1.4) => {
  const x = clamp(t) - 1;
  return x * x * ((s + 1) * x + s) + 1;
};

export type Ease = (t: number) => number;

/** a→b aralığında 0..1 ilerleme, yumuşatılmış. */
export const ramp = (t: number, a: number, b: number, ease: Ease = smootherstep) => ease(invLerp(a, b, t));

/**
 * Yumuşak zarf: start'ta 0'dan 1'e çıkar, end'de 1'den 0'a iner.
 * Hareketlerin başlangıç/bitişte sıçramamasını sağlar.
 */
export const envelope = (t: number, start: number, end: number, fadeIn = 0.35, fadeOut = 0.35) => {
  if (t <= start || t >= end) return 0;
  const a = fadeIn > 0 ? smootherstep((t - start) / fadeIn) : 1;
  const b = fadeOut > 0 ? smootherstep((end - t) / fadeOut) : 1;
  return Math.min(a, b);
};

export type Key<T> = readonly [number, T];

/** Anahtar kareler arasında yumuşak geçişli sayı enterpolasyonu. */
export const keys = (t: number, k: readonly Key<number>[], ease: Ease = smootherstep): number => {
  if (k.length === 0) return 0;
  if (t <= k[0][0]) return k[0][1];
  for (let i = 1; i < k.length; i++) {
    if (t <= k[i][0]) {
      const [t0, v0] = k[i - 1];
      const [t1, v1] = k[i];
      return lerp(v0, v1, ease(invLerp(t0, t1, t)));
    }
  }
  return k[k.length - 1][1];
};

export type Vec3 = readonly [number, number, number];

/** Anahtar kareler arasında yumuşak 3B vektör enterpolasyonu. */
export const keys3 = (t: number, k: readonly Key<Vec3>[], ease: Ease = smootherstep): [number, number, number] => [
  keys(t, k.map(([tt, v]) => [tt, v[0]] as const), ease),
  keys(t, k.map(([tt, v]) => [tt, v[1]] as const), ease),
  keys(t, k.map(([tt, v]) => [tt, v[2]] as const), ease),
];

/** Tohumlu sözde rastgele sayı üreteci (mulberry32). Her render'da aynı sonucu verir. */
export const rng = (seed: number) => {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
};

/** Sabit tohumdan tek bir değer (konuma bağlı rastgelelik için). */
export const hash = (n: number) => {
  const x = Math.sin(n * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
};

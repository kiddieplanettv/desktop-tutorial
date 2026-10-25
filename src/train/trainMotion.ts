import { smootherstep, lerp, invLerp } from '../animations/math';
import type { ResolvedTimeline } from '../timeline/timeline';

/**
 * Trenin bütün video boyunca hız ve konumu.
 * Hız anahtar kareleri yumuşak geçişlidir; konum hızın sayısal integralidir.
 * Böylece tekerlek dönüşü (mesafe / yarıçap) ile yer değiştirme her zaman uyumludur
 * ve sahne değişimlerinde tren sıçramaz.
 */
export interface TrainMotion {
  speedAt: (sec: number) => number;
  distanceAt: (sec: number) => number;
  /** Buhar bulutlarının çıkış zamanları (genel saniye). */
  steamTimes: number[];
}

const STEP = 1 / 240;

const cache = new WeakMap<ResolvedTimeline, TrainMotion>();

export const getTrainMotion = (tl: ResolvedTimeline): TrainMotion => {
  const hit = cache.get(tl);
  if (hit) return hit;

  const keys = tl.raw.train.speedKeys
    .map((k) => ({ t: tl.sceneTime(k), v: k.v }))
    .sort((a, b) => a.t - b.t);

  const speedAt = (sec: number) => {
    if (keys.length === 0) return 0;
    if (sec <= keys[0].t) return keys[0].v;
    for (let i = 1; i < keys.length; i++) {
      if (sec <= keys[i].t) {
        return lerp(keys[i - 1].v, keys[i].v, smootherstep(invLerp(keys[i - 1].t, keys[i].t, sec)));
      }
    }
    return keys[keys.length - 1].v;
  };

  // Hızın integrali: tablo 0..toplam süre arası, sabit adımla (deterministik).
  const n = Math.ceil(tl.totalSec / STEP) + 2;
  const table = new Float64Array(n);
  for (let i = 1; i < n; i++) {
    const t0 = (i - 1) * STEP;
    // trapez kuralı
    table[i] = table[i - 1] + ((speedAt(t0) + speedAt(t0 + STEP)) / 2) * STEP;
  }
  const raw = (sec: number) => {
    const x = Math.max(0, sec) / STEP;
    const i = Math.min(n - 2, Math.floor(x));
    const f = Math.min(1, x - i);
    return lerp(table[i], table[i + 1], f);
  };
  const anchor = tl.raw.train.anchor;
  const offset = anchor.distance - raw(tl.sceneTime(anchor));
  const distanceAt = (sec: number) => raw(sec) + offset;

  // Buhar: açıkça belirtilenler + belirli andan sonra her N birimde bir.
  const steamTimes = tl.raw.steam.explicit.map((r) => tl.sceneTime(r));
  const autoFrom = tl.sceneTime(tl.raw.steam.autoFrom);
  const every = tl.raw.steam.autoEveryDistance;
  if (every > 0) {
    let next = distanceAt(autoFrom) + every;
    for (let t = autoFrom; t <= tl.totalSec; t += STEP) {
      if (distanceAt(t) >= next) {
        steamTimes.push(t);
        next += every;
      }
    }
  }
  steamTimes.sort((a, b) => a - b);

  const motion = { speedAt, distanceAt, steamTimes };
  cache.set(tl, motion);
  return motion;
};

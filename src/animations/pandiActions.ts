import type { PoseDelta } from '../characters/pose';
import { clamp, envelope, hash, smootherstep, ramp } from './math';

/**
 * PANDİ'NİN 12 EYLEMİ
 * Her fonksiyon saniye cinsinden zamana (t) bağlıdır ve yalnızca bir PoseDelta döndürür.
 * Eylemler birbirinden bağımsızdır: istenen eylemler composePose(...) ile birleştirilir.
 * Pencereli eylemler (start/end) yumuşak zarf kullanır; bitişte poz sıçramaz.
 */

export interface Window {
  start: number;
  end: number;
  fadeIn?: number;
  fadeOut?: number;
}
const w = (t: number, win: Window) => envelope(t, win.start, win.end, win.fadeIn ?? 0.35, win.fadeOut ?? 0.35);

/** 1. Göz kırpma — tohumlu, düzensiz ama tekrarlanabilir aralıklarla. */
export const blink = (t: number, seed = 1): PoseDelta => {
  // 2.6–4.6 sn aralıklarla 0.2 sn süren kırpışlar
  let tt = 0.8 + hash(seed) * 1.5;
  let i = 0;
  while (tt < t - 0.25) {
    tt += 2.6 + hash(seed * 31 + i) * 2.0;
    i++;
  }
  const d = t - tt;
  if (d < 0 || d > 0.2) return {};
  const v = d < 0.08 ? d / 0.08 : 1 - (d - 0.08) / 0.12;
  return { blink: clamp(v) };
};

/** 2. Gülümseme — amount: -1..1 (nötr gülümsemeye göre fark). */
export const smile = (amount: number): PoseDelta => ({ smile: 0.25 * amount, mouthOpen: 0.35 * amount });

/** 3. Kolları kaldırma (sevinç). */
export const raiseArms = (t: number, win: Window): PoseDelta => {
  const k = w(t, win);
  const bob = Math.sin((t - win.start) * Math.PI * 2 * 1.2) * 0.12 * k;
  return {
    armL: { raise: 2.0 * k + bob, forward: -0.4 * k },
    armR: { raise: 2.0 * k - bob, forward: -0.4 * k },
    smile: 0.25 * k,
    mouthOpen: 0.3 * k,
  };
};

/** 4. El sallama — sağ veya sol kol. */
export const wave = (t: number, win: Window, side: 'L' | 'R' = 'R', speedHz = 1.6): PoseDelta => {
  const k = w(t, { fadeIn: 0.45, fadeOut: 0.45, ...win });
  const osc = Math.sin((t - win.start) * Math.PI * 2 * speedHz);
  // Kol yana-yukarı ve hafif öne: pati büyük kafanın arkasında kalmaz, yanağın yanında görünür.
  const arm = { raise: k * (1.95 + 0.3 * osc), forward: -k * 0.55, twist: k * 0.35 * osc };
  return {
    [side === 'R' ? 'armR' : 'armL']: arm,
    headRoll: k * 0.06 * osc * (side === 'R' ? 1 : -1),
    bodyRoll: k * 0.03 * osc,
    smile: 0.2 * k,
    mouthOpen: 0.25 * k,
  } as PoseDelta;
};

/** 5. Sağa/sola bakma — yaw (radyan, + = Pandi'nin soluna). */
export const look = (t: number, keysYaw: readonly (readonly [number, number])[]): PoseDelta => {
  if (!keysYaw.length) return {};
  let v = keysYaw[0][1];
  for (let i = 1; i < keysYaw.length; i++) {
    const [t0, v0] = keysYaw[i - 1];
    const [t1, v1] = keysYaw[i];
    if (t >= t0) v = v0 + (v1 - v0) * smootherstep((t - t0) / Math.max(0.001, t1 - t0));
  }
  return { headYaw: v };
};

/** 6. Kafayı hafifçe yana eğme (sevimli bakış). */
export const tilt = (t: number, win: Window, amount = 0.2): PoseDelta => {
  const k = w(t, { fadeIn: 0.5, fadeOut: 0.5, ...win });
  return { headRoll: amount * k, headPitch: 0.04 * k, browRaise: 0.4 * k };
};

/**
 * 7. Mutlu zıplama — hazırlık (çömelme), havalanma, iniş esnemesi.
 * Gerçek bir zıplama eğrisi: ekranda kaydırma değil.
 */
export const hop = (t: number, start: number, height = 0.5, airTime = 0.55): PoseDelta => {
  const prep = 0.16;
  const land = 0.18;
  const d = t - start;
  if (d < 0 || d > prep + airTime + land) return {};
  if (d < prep) {
    const k = Math.sin((d / prep) * Math.PI * 0.5);
    return { squash: -0.12 * k, armL: { raise: -0.05 * k }, armR: { raise: -0.05 * k } };
  }
  if (d < prep + airTime) {
    const u = (d - prep) / airTime;
    const y = 4 * u * (1 - u) * height; // parabol
    const stretch = 0.08 * Math.sin(u * Math.PI) * (1 - u);
    return {
      lift: y,
      squash: stretch,
      armL: { raise: 0.9 * Math.sin(u * Math.PI) },
      armR: { raise: 0.9 * Math.sin(u * Math.PI) },
      legL: -0.25 * Math.sin(u * Math.PI),
      legR: 0.25 * Math.sin(u * Math.PI),
      smile: 0.25,
      mouthOpen: 0.3,
    };
  }
  const u = (d - prep - airTime) / land;
  return { squash: -0.1 * Math.sin(u * Math.PI) };
};

/** 8. Direksiyonu tutma — kollar öne, direksiyon hafifçe sağa sola. Kollar ayrı ayrı bırakılabilir. */
export const steer = (t: number, amountL: number, amountR = amountL, turn = 0): PoseDelta => {
  const kl = clamp(amountL);
  const kr = clamp(amountR);
  const wobble = Math.sin(t * 1.3) * 0.05 + turn;
  return {
    armL: { raise: -0.1 * kl + wobble * kl * 0.4, forward: 1.12 * kl + wobble * 0.25 * kl },
    armR: { raise: -0.1 * kr - wobble * kr * 0.4, forward: 1.12 * kr - wobble * 0.25 * kr },
    bodyPitch: 0.06 * Math.max(kl, kr),
  };
};

/** Direksiyon simidinin dönüş açısı (steer ile aynı salınım). */
export const steeringWheelTurn = (t: number, amount: number, turn = 0) => clamp(amount) * (Math.sin(t * 1.3) * 0.05 + turn) * 2.2;

/** 9. Şaşırma — kaşlar kalkar, ağız "O" olur, gözler büyür. */
export const surprise = (t: number, win: Window): PoseDelta => {
  const k = w(t, { fadeIn: 0.15, fadeOut: 0.4, ...win });
  return { surprise: k, browRaise: k, headPitch: -0.08 * k, bodyPitch: -0.05 * k, lift: 0.04 * k };
};

/**
 * 10. Başını ritme göre sallama.
 * bpm null ise (şarkı henüz yok) yavaş, sakin bir varsayılan tempo kullanılır.
 */
export const DEFAULT_BPM = 100;
export const beatPhase = (t: number, bpm: number | null, beatOffsetSec = 0) =>
  ((t - beatOffsetSec) * (bpm ?? DEFAULT_BPM)) / 60;
export const nodToBeat = (t: number, win: Window, bpm: number | null, beatOffsetSec = 0): PoseDelta => {
  const k = w(t, win);
  const ph = beatPhase(t, bpm, beatOffsetSec);
  return { headPitch: 0.09 * k * Math.sin(ph * Math.PI * 2), headRoll: 0.04 * k * Math.sin(ph * Math.PI) };
};

/** 11. Hafif dans — yana salınma, küçük sekme, kollar ritimle. */
export const dance = (t: number, win: Window, bpm: number | null, beatOffsetSec = 0): PoseDelta => {
  const k = w(t, { fadeIn: 0.5, fadeOut: 0.5, ...win });
  const ph = beatPhase(t, bpm, beatOffsetSec);
  const s = Math.sin(ph * Math.PI); // iki vuruşta bir sağ-sol
  const bounce = Math.abs(Math.sin(ph * Math.PI));
  return {
    bodyRoll: 0.12 * s * k,
    headRoll: -0.08 * s * k,
    lift: 0.06 * bounce * k,
    squash: -0.03 * (1 - bounce) * k,
    armL: { raise: (0.7 + 0.35 * s) * k, forward: 0.3 * k },
    armR: { raise: (0.7 - 0.35 * s) * k, forward: 0.3 * k },
    legL: 0.12 * s * k,
    legR: -0.12 * s * k,
    smile: 0.25 * k,
    mouthOpen: 0.3 * k,
  };
};

/** 12. Seyirciye dönüp selamlama — dön, hafif eğil, el salla. */
export const greet = (t: number, win: Window, facingYaw: number): PoseDelta => {
  const k = w(t, { fadeIn: 0.6, fadeOut: 0.6, ...win });
  const bow = envelope(t, win.start + 0.5, win.start + 1.6, 0.4, 0.4);
  return {
    bodyYaw: -facingYaw * k,
    bodyPitch: 0.18 * bow,
    headPitch: 0.15 * bow,
    ...wave(t, { start: win.start + 1.2, end: win.end }, 'R'),
  };
};

/** Yürüme döngüsü — adım fazı yol mesafesinden gelir, böylece ayaklar kaymaz. */
export const walkCycle = (distance: number, amount: number, stride = 0.62): PoseDelta => {
  const k = clamp(amount);
  const ph = (distance / stride) * Math.PI;
  const s = Math.sin(ph);
  return {
    legL: 0.5 * s * k,
    legR: -0.5 * s * k,
    armL: { forward: -0.35 * s * k },
    armR: { forward: 0.35 * s * k },
    lift: 0.05 * Math.abs(Math.cos(ph)) * k,
    bodyRoll: 0.05 * s * k,
    headRoll: -0.03 * s * k,
  };
};

/** Pozlar arası yumuşak ağırlık (ör. ayakta → oturma). */
export const weight = (t: number, a: number, b: number) => ramp(t, a, b);

/**
 * Pandi'nin tüm kontrol edilebilir parametreleri.
 * Her eylem (el sallama, zıplama, ...) bu değerlere küçük eklemeler yapar;
 * böylece hareketler birbirinden bağımsız açılıp kapatılabilir ve birleştirilebilir.
 */
export interface ArmPose {
  /** Yana kaldırma (radyan). 0 = aşağı sarkık, ~2.6 = yukarıda. */
  raise: number;
  /** Öne uzatma (radyan). ~1.4 = tam öne. */
  forward: number;
  /** Pati dönüşü (radyan). */
  twist: number;
}

export interface PandiPose {
  blink: number; // 0 açık, 1 kapalı
  smile: number; // 0 nötr, 1 geniş gülümseme
  mouthOpen: number; // 0 kapalı, 1 açık
  surprise: number; // 0..1, ağız "O" ve gözler büyür
  browRaise: number; // 0..1
  headYaw: number; // sağa/sola bakma
  headPitch: number; // öne/arkaya (+ öne eğilir)
  headRoll: number; // yana eğme
  bodyYaw: number; // tüm karakteri döndürme
  bodyPitch: number; // öne eğilme (+ öne)
  bodyRoll: number; // yana salınma
  lift: number; // dikey ofset (zıplama)
  squash: number; // + uzama, - basılma
  armL: ArmPose;
  armR: ArmPose;
  legL: number; // bacak öne/arkaya salınım
  legR: number;
  sit: number; // 0 ayakta, 1 oturuyor (bacaklar öne)
}

export const NEUTRAL_POSE: PandiPose = {
  blink: 0,
  smile: 0.75,
  mouthOpen: 0.55,
  surprise: 0,
  browRaise: 0,
  headYaw: 0,
  headPitch: 0,
  headRoll: 0,
  bodyYaw: 0,
  bodyPitch: 0,
  bodyRoll: 0,
  lift: 0,
  squash: 0,
  armL: { raise: 0.22, forward: 0.15, twist: 0 },
  armR: { raise: 0.22, forward: 0.15, twist: 0 },
  legL: 0,
  legR: 0,
  sit: 0,
};

export type PoseDelta = {
  [K in keyof PandiPose]?: PandiPose[K] extends ArmPose ? Partial<ArmPose> : number;
};

const addArm = (a: ArmPose, d?: Partial<ArmPose>): ArmPose =>
  d
    ? { raise: a.raise + (d.raise ?? 0), forward: a.forward + (d.forward ?? 0), twist: a.twist + (d.twist ?? 0) }
    : a;

/** Eylemlerden gelen farkları nötr poza ekler ve sınırlandırır. */
export const composePose = (...deltas: PoseDelta[]): PandiPose => {
  const p: PandiPose = { ...NEUTRAL_POSE, armL: { ...NEUTRAL_POSE.armL }, armR: { ...NEUTRAL_POSE.armR } };
  for (const d of deltas) {
    for (const k of Object.keys(d) as (keyof PandiPose)[]) {
      if (k === 'armL' || k === 'armR') {
        p[k] = addArm(p[k], d[k] as Partial<ArmPose>);
      } else {
        (p[k] as number) += (d[k] as number) ?? 0;
      }
    }
  }
  const c01 = (v: number) => Math.min(1, Math.max(0, v));
  p.blink = c01(p.blink);
  p.smile = c01(p.smile);
  p.mouthOpen = c01(p.mouthOpen);
  p.surprise = c01(p.surprise);
  p.browRaise = c01(p.browRaise);
  p.sit = c01(p.sit);
  // Kolların gövdeye girmemesi için alt sınır.
  p.armL.raise = Math.max(0.12, p.armL.raise);
  p.armR.raise = Math.max(0.12, p.armR.raise);
  return p;
};

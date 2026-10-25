import rawTiming from './timing.json';

export type SceneId = string;

export interface SceneTiming {
  id: SceneId;
  durationSec: number;
  title: string;
  summary: string;
}

export interface SceneRef {
  scene: SceneId;
  /** Sahne içindeki oran, 0..1 */
  at: number;
}

export interface AudioTiming {
  src: string | null;
  startOffsetSec: number;
  volume: number;
  bpm: number | null;
  beatOffsetSec: number;
}

export interface TimingFile {
  fps: number;
  width: number;
  height: number;
  audio: AudioTiming;
  scenes: SceneTiming[];
  train: {
    speedKeys: (SceneRef & { v: number })[];
    anchor: SceneRef & { distance: number };
  };
  steam: {
    explicit: SceneRef[];
    autoFrom: SceneRef;
    autoEveryDistance: number;
  };
}

export interface ResolvedScene extends SceneTiming {
  index: number;
  number: number;
  startFrame: number;
  durationInFrames: number;
  endFrame: number;
  startSec: number;
  endSec: number;
}

export interface ResolvedTimeline {
  raw: TimingFile;
  fps: number;
  width: number;
  height: number;
  scenes: ResolvedScene[];
  totalFrames: number;
  totalSec: number;
  byId: Record<SceneId, ResolvedScene>;
  /** Sahne referansını (sahne + oran) videonun genel saniyesine çevirir. */
  sceneTime: (ref: SceneRef) => number;
}

export const DEFAULT_TIMING = rawTiming as unknown as TimingFile;

/**
 * Sahne sürelerinden başlangıç/bitiş karelerini hesaplar.
 * Sahneler arka arkaya dizildiği için arada boş veya siyah kare kalamaz.
 */
export const resolveTimeline = (timing: TimingFile = DEFAULT_TIMING): ResolvedTimeline => {
  const { fps } = timing;
  if (!timing.scenes.length) throw new Error('timing.json içinde hiç sahne yok.');
  let cursor = 0;
  const scenes: ResolvedScene[] = timing.scenes.map((s, index) => {
    if (!(s.durationSec > 0)) throw new Error(`Sahne ${s.id}: durationSec pozitif olmalı (şu an ${s.durationSec}).`);
    const durationInFrames = Math.round(s.durationSec * fps);
    const r: ResolvedScene = {
      ...s,
      index,
      number: index + 1,
      startFrame: cursor,
      durationInFrames,
      endFrame: cursor + durationInFrames,
      startSec: cursor / fps,
      endSec: (cursor + durationInFrames) / fps,
    };
    cursor += durationInFrames;
    return r;
  });
  const byId: Record<string, ResolvedScene> = {};
  for (const s of scenes) {
    if (byId[s.id]) throw new Error(`Sahne kimliği tekrar ediyor: ${s.id}`);
    byId[s.id] = s;
  }
  const sceneTime = (ref: SceneRef) => {
    const s = byId[ref.scene];
    if (!s) throw new Error(`timing.json: bilinmeyen sahne kimliği "${ref.scene}"`);
    return s.startSec + ref.at * (s.endSec - s.startSec);
  };
  return {
    raw: timing,
    fps,
    width: timing.width,
    height: timing.height,
    scenes,
    totalFrames: cursor,
    totalSec: cursor / fps,
    byId,
    sceneTime,
  };
};

const cache = new WeakMap<TimingFile, ResolvedTimeline>();
export const getTimeline = (timing: TimingFile = DEFAULT_TIMING) => {
  let t = cache.get(timing);
  if (!t) {
    t = resolveTimeline(timing);
    cache.set(timing, t);
  }
  return t;
};

export const formatTime = (sec: number) => {
  const m = Math.floor(sec / 60);
  const s = sec - m * 60;
  return `${String(m).padStart(2, '0')}:${s.toFixed(2).padStart(5, '0')}`;
};

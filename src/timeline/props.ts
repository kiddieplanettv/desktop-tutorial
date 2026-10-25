import { z } from 'zod';
import { DEFAULT_TIMING, type TimingFile } from './timeline';

/**
 * Remotion Studio'nun sağ panelinde düzenlenebilen ayarlar.
 * Varsayılanlar timing.json'dan gelir; kalıcı değişiklik için timing.json düzenlenmelidir.
 */
export const videoSchema = z.object({
  showGuides: z.boolean().describe('Sahne adı / zaman kodu katmanı (yalnızca kontrol için)'),
  audioEnabled: z.boolean().describe('Şarkıyı çal / dışa aktar'),
  audioSrc: z.string().describe("public/ altındaki ses dosyası, ör. 'audio/sarki.mp3' (boş = ses yok)"),
  audioStartOffsetSec: z.number().describe('Şarkının videodaki başlangıç kayması (sn)'),
  audioVolume: z.number().min(0).max(2),
  bpm: z.number().nullable().describe('Şarkının temposu (bilinmiyorsa boş)'),
  beatOffsetSec: z.number().describe('İlk vuruşun zamanı (sn)'),
  sceneDurationsSec: z.array(z.number().min(2).max(60)).describe('Sahne süreleri (sn), sırasıyla 1..21'),
});

export type VideoProps = z.infer<typeof videoSchema>;

export const defaultVideoProps: VideoProps = {
  showGuides: false,
  audioEnabled: false,
  audioSrc: DEFAULT_TIMING.audio.src ?? '',
  audioStartOffsetSec: DEFAULT_TIMING.audio.startOffsetSec,
  audioVolume: DEFAULT_TIMING.audio.volume,
  bpm: DEFAULT_TIMING.audio.bpm,
  beatOffsetSec: DEFAULT_TIMING.audio.beatOffsetSec,
  sceneDurationsSec: DEFAULT_TIMING.scenes.map((s) => s.durationSec),
};

const cache = new Map<string, TimingFile>();
/** Studio ayarlarını zamanlama dosyasıyla birleştirir (aynı ayarlar → aynı nesne). */
export const timingFromProps = (p: VideoProps): TimingFile => {
  const key = JSON.stringify(p);
  const hit = cache.get(key);
  if (hit) return hit;
  if (p.sceneDurationsSec.length !== DEFAULT_TIMING.scenes.length) {
    throw new Error(`sceneDurationsSec ${DEFAULT_TIMING.scenes.length} değer içermeli (şu an ${p.sceneDurationsSec.length}).`);
  }
  const t: TimingFile = {
    ...DEFAULT_TIMING,
    audio: {
      src: p.audioSrc.trim() === '' ? null : p.audioSrc.trim(),
      startOffsetSec: p.audioStartOffsetSec,
      volume: p.audioVolume,
      bpm: p.bpm,
      beatOffsetSec: p.beatOffsetSec,
    },
    scenes: DEFAULT_TIMING.scenes.map((s, i) => ({ ...s, durationSec: p.sceneDurationsSec[i] })),
  };
  cache.set(key, t);
  return t;
};

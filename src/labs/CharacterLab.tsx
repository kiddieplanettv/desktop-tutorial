import React from 'react';
import { z } from 'zod';
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from 'remotion';
import * as A from '../animations/pandiActions';
import { envelope } from '../animations/math';
import { Pandi } from '../characters/Pandi';
import { composePose, type PoseDelta } from '../characters/pose';
import { SceneCanvas } from '../scenes/SceneCanvas';
import { Ground } from '../environments/Ground';
import { Flowers } from '../environments/Nature';

export const ACTIONS = [
  'gozKirpma',
  'gulumseme',
  'kollariKaldirma',
  'elSallama',
  'sagaSolaBakma',
  'kafaEgme',
  'ziplama',
  'direksiyon',
  'sasirma',
  'ritimSallama',
  'dans',
  'selamlama',
] as const;

const LABELS: Record<(typeof ACTIONS)[number] | 'tumu', string> = {
  tumu: 'Tüm eylemler sırayla',
  gozKirpma: '1. Göz kırpma',
  gulumseme: '2. Gülümseme',
  kollariKaldirma: '3. Kollarını kaldırma',
  elSallama: '4. El sallama',
  sagaSolaBakma: '5. Sağa ve sola bakma',
  kafaEgme: '6. Kafasını hafifçe eğme',
  ziplama: '7. Mutlu zıplama',
  direksiyon: '8. Direksiyonu tutma',
  sasirma: '9. Şaşırma',
  ritimSallama: '10. Başını ritme göre sallama',
  dans: '11. Hafifçe dans etme',
  selamlama: '12. Seyirciye dönerek selamlama',
};

export const characterLabSchema = z.object({
  action: z.enum(['tumu', ...ACTIONS]),
  turntable: z.boolean().describe('Karakteri yavaşça döndür (her açıdan kontrol)'),
  kamera: z.enum(['tam', 'yakin']).describe('Tam boy veya yüz yakın plan'),
  bpm: z.number().nullable(),
});
export type CharacterLabProps = z.infer<typeof characterLabSchema>;

export const ACTION_SEC = 4;

const actionDelta = (name: (typeof ACTIONS)[number], t: number, bpm: number | null): PoseDelta[] => {
  const win = { start: 0.3, end: ACTION_SEC - 0.3 };
  switch (name) {
    case 'gozKirpma':
      return [{ blink: Math.max(envelope(t, 0.8, 1.05, 0.08, 0.12), envelope(t, 2.4, 2.65, 0.08, 0.12)) }];
    case 'gulumseme':
      return [A.smile(Math.sin((t / ACTION_SEC) * Math.PI) * 1.2 - 0.6)];
    case 'kollariKaldirma':
      return [A.raiseArms(t, win)];
    case 'elSallama':
      return [A.wave(t, win, 'R')];
    case 'sagaSolaBakma':
      return [A.look(t, [[0.3, 0], [1.0, 0.8], [2.0, 0.8], [2.8, -0.8], [3.5, -0.8], [3.9, 0]])];
    case 'kafaEgme':
      return [A.tilt(t, win, 0.25)];
    case 'ziplama':
      return [A.hop(t, 0.6, 0.5), A.hop(t, 2.0, 0.5)];
    case 'direksiyon':
      return [A.steer(t, envelope(t, 0.3, 3.7, 0.5, 0.5), undefined, Math.sin(t * 2) * 0.15)];
    case 'sasirma':
      return [A.surprise(t, { start: 0.8, end: 3.0 })];
    case 'ritimSallama':
      return [A.nodToBeat(t, win, bpm)];
    case 'dans':
      return [A.dance(t, win, bpm)];
    case 'selamlama':
      return [A.greet(t, win, 0.9)];
  }
};

/** Pandi'nin 12 eylemini tek tek veya sırayla gösteren kontrol sahnesi. */
export const CharacterLab: React.FC<CharacterLabProps> = ({ action, turntable, kamera, bpm }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const sec = frame / fps;
  const current = action === 'tumu' ? ACTIONS[Math.min(ACTIONS.length - 1, Math.floor(sec / ACTION_SEC))] : action;
  const lt = action === 'tumu' ? sec % ACTION_SEC : sec % ACTION_SEC;
  const extraYaw = current === 'selamlama' ? 0.9 : 0;
  const pose = composePose(A.blink(sec, 3), ...actionDelta(current, lt, bpm), { bodyYaw: extraYaw });
  const spin = turntable ? (sec / 12) * Math.PI * 2 : 0;
  const flowers = React.useMemo(
    () =>
      Array.from({ length: 40 }, (_, i) => ({
        x: Math.cos(i * 2.4) * (3 + (i % 5) * 0.6),
        z: Math.sin(i * 2.4) * (3 + (i % 5) * 0.6) - 1,
        color: ['#FF6B6B', '#FFD93D', '#6BCBFF', '#C38BFF', '#FF9F43'][i % 5],
      })),
    [],
  );
  return (
    <AbsoluteFill>
      <SceneCanvas
        camera={kamera === 'yakin' ? { position: [0, 1.75, 3.6], target: [0, 1.45, 0], fov: 30 } : { position: [0, 2.0, 7.2], target: [0, 1.25, 0], fov: 34 }}
        focus={[0, 0, 0]}
      >
        <Ground center={[0, 0]} size={200} />
        <Flowers items={flowers} time={sec} />
        <Pandi pose={pose} rotation={[0, spin, 0]} />
      </SceneCanvas>
      <div
        style={{
          position: 'absolute',
          left: 40,
          bottom: 40,
          background: '#0B1530CC',
          color: 'white',
          fontFamily: 'Nunito, system-ui, sans-serif',
          fontSize: 40,
          fontWeight: 800,
          padding: '14px 28px',
          borderRadius: 18,
        }}
      >
        {LABELS[current]}
      </div>
    </AbsoluteFill>
  );
};

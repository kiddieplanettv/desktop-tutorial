import React from 'react';
import { z } from 'zod';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { SceneCanvas } from '../scenes/SceneCanvas';
import { Ground } from '../environments/Ground';
import { Rails } from '../environments/Rails';
import { Train } from '../train/Train';
import { Steam } from '../train/Steam';
import { Pandi } from '../characters/Pandi';
import { composePose } from '../characters/pose';
import { blink, steer } from '../animations/pandiActions';
import { LOCO, carTransforms } from '../train/layout';
import { getTrack } from '../train/track';

export const trainLabSchema = z.object({
  speed: z.number().min(0).max(15).describe('Tren hızı (birim/sn)'),
  camera: z.enum(['yan', 'onCapraz', 'yorunge', 'kabin']),
  steam: z.boolean(),
});
export type TrainLabProps = z.infer<typeof trainLabSchema>;

/** Tren, tekerlek, vagon bağlantısı ve buhar testi. Viraj içeren ray bölümünde koşar. */
export const TrainLab: React.FC<TrainLabProps> = ({ speed, camera, steam }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const track = getTrack();
  const distanceAt = (sec: number) => 380 + sec * speed;
  const d = distanceAt(t);
  const loco = carTransforms(track, d)[0];
  const lp = loco.position;
  const steamTimes = steam && speed > 0 ? Array.from({ length: Math.ceil((t + 1) * speed / 2.6) }, (_, i) => (i * 2.6) / Math.max(0.01, speed)) : [];
  const cams: Record<TrainLabProps['camera'], { position: [number, number, number]; target: [number, number, number]; fov: number }> = {
    yan: { position: [lp.x - 8, 4, lp.z + 22], target: [lp.x - 10, 1.8, lp.z], fov: 42 },
    onCapraz: { position: [lp.x + 12, 4.5, lp.z + 11], target: [lp.x - 2, 2, lp.z], fov: 40 },
    yorunge: {
      position: [lp.x + Math.cos(t * 0.4) * 16, 6, lp.z + Math.sin(t * 0.4) * 16],
      target: [lp.x - 6, 1.8, lp.z],
      fov: 45,
    },
    kabin: { position: [lp.x - 2, 3.4, lp.z + 6], target: [lp.x - 2, 2.2, lp.z], fov: 40 },
  };
  const pose = composePose({ sit: 1 }, blink(t, 5), steer(t, 1));
  return (
    <SceneCanvas camera={cams[camera]} focus={[lp.x - 8, 0, lp.z]}>
      <Ground center={[lp.x, lp.z]} />
      <Rails track={track} from={300} to={560} />
      <Train track={track} distance={d} speed={speed} time={t} cab={<Pandi pose={pose} position={LOCO.seat.toArray()} rotation={[0, Math.PI / 2, 0]} />} />
      <Steam track={track} time={t} emitTimes={steamTimes} distanceAt={distanceAt} />
    </SceneCanvas>
  );
};

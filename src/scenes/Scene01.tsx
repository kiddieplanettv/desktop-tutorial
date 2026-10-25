import React from 'react';
import { keys, keys3, ramp } from '../animations/math';
import { blink, hop, look, smile, tilt, wave } from '../animations/pandiActions';
import { Pandi } from '../characters/Pandi';
import { composePose } from '../characters/pose';
import { FIRST_STATION, StationValley } from '../environments/StationValley';
import { getTrack } from '../train/track';
import { getTrainMotion } from '../train/trainMotion';
import { Train } from '../train/Train';
import { Steam } from '../train/Steam';
import { SceneCanvas } from './SceneCanvas';
import type { SceneProps } from './types';
import { useSceneClock } from './useSceneClock';

/**
 * SAHNE 1 — 00:00–00:10 — İstasyonda günaydın
 * Güneşli sabah, renkli istasyon. Sarı lokomotif uzaktan gelir ve istasyonda durur.
 * Pandi kameraya döner, gülümser, el sallar. Kamera yavaşça Pandi'ye yaklaşır.
 */
export const SCENE01_CAMERA_END = {
  position: [4.2, 2.6, 10.5] as [number, number, number],
  target: [1.6, 2.0, 3.6] as [number, number, number],
  fov: 38,
};
export const SCENE01_PANDI_END_YAW = 0.38;

export const Scene01: React.FC<SceneProps> = (props) => {
  const { t, lt } = useSceneClock(props);
  const track = getTrack();
  const motion = getTrainMotion(props.tl);
  const distance = motion.distanceAt(t);

  // Kamera: geniş açıdan (uzaktaki tren görünür) Pandi'ye yavaş yaklaşma.
  const camPos = keys3(lt, [
    [0, [10, 3.6, 20]],
    [2.0, [9.2, 3.4, 18.6]],
    [10, SCENE01_CAMERA_END.position],
  ]);
  const camTarget = keys3(lt, [
    [0, [-8, 2.0, 0]],
    [2.0, [-5.5, 2.0, 0.6]],
    [10, SCENE01_CAMERA_END.target],
  ]);
  const fov = keys(lt, [
    [0, 42],
    [10, SCENE01_CAMERA_END.fov],
  ]);

  // Pandi koreografisi
  const pose = composePose(
    { bodyYaw: keys(lt, [[0, 0.15], [1.6, 0.15], [2.4, 0.45], [10, SCENE01_PANDI_END_YAW]]) },
    look(lt, [[0, -0.75], [1.4, -0.75], [2.2, 0.08], [6.6, 0.0]]),
    smile(keys(lt, [[0, -0.4], [1.8, -0.4], [2.5, 0.6], [10, 0.4]])),
    blink(t, 1),
    wave(lt, { start: 2.5, end: 6.6 }, 'R'),
    tilt(lt, { start: 6.7, end: 8.2 }, 0.22),
    hop(lt, 8.4, 0.38, 0.5),
    // tren yanaşırken kısa merak (kaşlar)
    { browRaise: 0.5 * ramp(lt, 0.2, 0.8) * (1 - ramp(lt, 1.6, 2.2)) },
  );

  return (
    <SceneCanvas camera={{ position: camPos, target: camTarget, fov }} focus={[0, 0, 2]}>
      <StationValley track={track} time={t} focusX={0} />
      <Train track={track} distance={distance} speed={motion.speedAt(t)} time={t} />
      <Steam track={track} time={t} emitTimes={motion.steamTimes} distanceAt={motion.distanceAt} />
      <Pandi pose={pose} position={FIRST_STATION.pandiSpot} />
    </SceneCanvas>
  );
};

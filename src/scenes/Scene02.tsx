import React from 'react';
import * as THREE from 'three';
import { envelope, keys, keys3, lerp, ramp, smootherstep } from '../animations/math';
import { blink, look, nodToBeat, smile, steer, steeringWheelTurn, surprise, walkCycle, wave } from '../animations/pandiActions';
import { Pandi } from '../characters/Pandi';
import { composePose } from '../characters/pose';
import { FIRST_STATION, StationValley } from '../environments/StationValley';
import { LOCO, carLocalToWorld, carTransforms } from '../train/layout';
import { getTrack } from '../train/track';
import { getTrainMotion } from '../train/trainMotion';
import { Train } from '../train/Train';
import { Steam } from '../train/Steam';
import { SceneCanvas } from './SceneCanvas';
import { SCENE01_CAMERA_END, SCENE01_PANDI_END_YAW } from './Scene01';
import type { SceneProps } from './types';
import { useSceneClock } from './useSceneClock';

/**
 * SAHNE 2 — 00:10–00:20 — Pandi sürücü koltuğunda
 * Pandi perondan yürür, zıplayarak kabine geçer ve direksiyonu tutar.
 * Tren hafifçe sallanır, bacadan üç küçük buhar bulutu çıkar, tekerlekler yavaşça dönmeye başlar.
 */

// Koreografi zamanları (nominal saniye)
const T = {
  turnStart: 0.2,
  walkStart: 0.6,
  walkEnd: 2.6,
  hopStart: 2.75,
  hopEnd: 3.85,
  grab: 4.0,
} as const;

export const Scene02: React.FC<SceneProps> = (props) => {
  const { t, lt } = useSceneClock(props);
  const track = getTrack();
  const motion = getTrainMotion(props.tl);
  const distance = motion.distanceAt(t);
  const loco = carTransforms(track, distance)[0];

  // --- Pandi'nin dünyadaki yolu (perondan kabine) ---
  const start = new THREE.Vector3(...FIRST_STATION.pandiSpot);
  const edge = new THREE.Vector3(2.95, FIRST_STATION.platformTop, 2.15);
  // Zıplama sırasında tren durmaktadır; koltuğun dünya konumu zıplama anındaki lokomotiften alınır.
  const seatWorld = carLocalToWorld(carTransforms(track, motion.distanceAt(props.scene.startSec + (T.hopEnd / 10) * (props.scene.endSec - props.scene.startSec)))[0], LOCO.seat);

  const walkK = ramp(lt, T.walkStart, T.walkEnd, (x) => x); // doğrusal: adım fazı mesafeden
  const walkEase = smootherstep(walkK);
  const walkPos = start.clone().lerp(edge, walkEase);
  const walkedDist = start.distanceTo(edge) * walkEase;
  const walking = envelope(lt, T.walkStart, T.walkEnd, 0.3, 0.3);

  const hopU = ramp(lt, T.hopStart, T.hopEnd, (x) => x);
  const inAir = lt >= T.hopStart && lt < T.hopEnd;
  const seated = lt >= T.hopEnd;

  let worldPos = walkPos;
  if (lt >= T.hopStart) {
    const u = smootherstep(hopU);
    worldPos = edge.clone().lerp(seatWorld, u);
    worldPos.y += 4 * hopU * (1 - hopU) * 0.62; // parabol: alçak duvarın üzerinden
  }

  const walkYaw = Math.atan2(edge.x - start.x, edge.z - start.z);
  const bodyYaw = keys(lt, [
    [0, SCENE01_PANDI_END_YAW],
    [T.turnStart, SCENE01_PANDI_END_YAW],
    [T.walkStart + 0.3, walkYaw],
    [T.walkEnd, walkYaw],
    [T.hopStart, Math.PI],
    [T.hopEnd, Math.PI / 2],
  ]);

  // Oturma, zıplamanın ilk yarısında başlar (bacaklar öne toplanır).
  const sit = ramp(lt, T.hopStart + 0.1, T.hopStart + 0.6);
  const crouch = inAir ? -0.1 * Math.sin(hopU * Math.PI) : 0;
  const preHop = envelope(lt, T.hopStart - 0.2, T.hopStart + 0.05, 0.15, 0.05);
  const landing = envelope(lt, T.hopEnd - 0.02, T.hopEnd + 0.3, 0.02, 0.25);

  const steerK = ramp(lt, T.grab, T.grab + 0.7);
  const waveL = envelope(lt, 7.3, 9.4, 0.5, 0.5);

  const pose = composePose(
    { bodyYaw: seated ? 0 : bodyYaw, sit, squash: crouch - 0.12 * preHop - 0.1 * landing },
    walkCycle(walkedDist, walking),
    inAir ? { armL: { raise: 0.9 * Math.sin(hopU * Math.PI) }, armR: { raise: 0.9 * Math.sin(hopU * Math.PI) }, smile: 0.25, mouthOpen: 0.3 } : {},
    blink(t, 2),
    // kabinde: kameraya bakıp gülümseme
    look(lt, [[0, 0.0], [T.hopEnd, 0.0], [4.6, -0.95], [6.2, -0.95], [6.8, -0.2], [7.3, -1.0], [9.6, -0.9]]),
    smile(keys(lt, [[0, 0.4], [4.6, 0.5], [10, 0.6]])),
    steer(lt, steerK, steerK * (1 - waveL)),
    surprise(lt, { start: 4.95, end: 5.6 }),
    nodToBeat(lt, { start: 5.9, end: 7.2 }, props.tl.raw.audio.bpm),
    wave(lt, { start: 7.3, end: 9.4 }, 'R'),
  );

  // Kamera: Sahne 1'in bittiği yerden devam eder (sıçrama yok), Pandi'yi izler, sonra lokomotifi ve buharı gösterir.
  const camPos = keys3(lt, [
    [0, SCENE01_CAMERA_END.position],
    [1.0, SCENE01_CAMERA_END.position],
    [4.2, [6.6, 3.2, 9.6]],
    [6.5, [9.6, 3.9, 12.5]],
    [10, [11.6, 3.7, 12.8]],
  ]);
  const camTarget = keys3(lt, [
    [0, SCENE01_CAMERA_END.target],
    [1.0, SCENE01_CAMERA_END.target],
    [4.2, [2.9, 2.4, 0.6]],
    [6.5, [4.2, 2.8, 0]],
    [10, [6.4, 2.6, 0]],
  ]);
  const fov = keys(lt, [
    [0, SCENE01_CAMERA_END.fov],
    [4.2, 36],
    [10, 40],
  ]);

  const idleRock = envelope(lt, 4.6, 7.6, 0.6, 0.8);
  const pandiLocal = LOCO.seat;
  const pandiNode = <Pandi pose={pose} position={seated ? pandiLocal.toArray() : worldPos.toArray()} rotation={seated ? [0, Math.PI / 2, 0] : undefined} />;

  return (
    <SceneCanvas camera={{ position: camPos, target: camTarget, fov }} focus={[lerp(2, loco.position.x, 0.5), 0, 1]}>
      <StationValley track={track} time={t} focusX={0} />
      <Train
        track={track}
        distance={distance}
        speed={motion.speedAt(t)}
        idleRock={idleRock}
        time={t}
        cab={seated ? pandiNode : undefined}
        steeringTurn={steeringWheelTurn(lt, steerK)}
      />
      {!seated && pandiNode}
      <Steam track={track} time={t} emitTimes={motion.steamTimes} distanceAt={motion.distanceAt} />
    </SceneCanvas>
  );
};

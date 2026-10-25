import React, { useMemo } from 'react';
import * as THREE from 'three';
import { between } from '../assets/geometry';
import { Locomotive } from './Locomotive';
import { Wagon } from './Wagon';
import { CARS, WAGON_COLORS, carLocalToWorld, carTransforms } from './layout';
import { paint } from './materials';
import type { Track } from './track';

export interface TrainProps {
  track: Track;
  /** Lokomotif önünün ray üzerindeki mesafesi. */
  distance: number;
  /** Anlık hız (birim/sn) — salınım şiddeti buna bağlıdır. */
  speed: number;
  /** Ek motor titreşimi (0..1), ör. kalkıştan önce. */
  idleRock?: number;
  /** Video zamanı (sn) — salınım fazı için. */
  time: number;
  cab?: React.ReactNode;
  riders?: (React.ReactNode | undefined)[];
  glow?: number[];
  steeringTurn?: number;
}

/**
 * Lokomotif + 6 renkli vagon. Her araç ray üzerinde iki boji noktasına oturur,
 * bağlantı kolları iki araç arasındaki gerçek uç noktalarından hesaplanır (kopmaz, içe geçmez).
 */
export const Train: React.FC<TrainProps> = ({ track, distance, speed, idleRock = 0, time, cab, riders = [], glow = [], steeringTurn }) => {
  const transforms = useMemo(() => carTransforms(track, distance), [track, distance]);
  const sway = Math.min(1, Math.abs(speed) / 6);

  const couplers = useMemo(() => {
    const out: { mid: THREE.Vector3; quat: THREE.Quaternion; len: number }[] = [];
    for (let i = 0; i < CARS.length - 1; i++) {
      const a = carLocalToWorld(transforms[i], new THREE.Vector3(CARS[i].rear, 0.9, 0));
      const b = carLocalToWorld(transforms[i + 1], new THREE.Vector3(CARS[i + 1].front, 0.9, 0));
      out.push(between(a, b));
    }
    return out;
  }, [transforms]);

  const couplerMat = paint('#1E1A1C', { roughness: 0.4 });

  return (
    <group>
      {CARS.map((car, i) => {
        const t = transforms[i];
        // yumuşak, küçük yan salınım (sahne değişiminde süreklidir: zaman ve mesafeye bağlı)
        const roll =
          sway * 0.018 * Math.sin(distance * 0.55 + i * 1.7) +
          idleRock * 0.022 * Math.sin(time * 9 + i * 0.6) * (car.kind === 'loco' ? 1 : 0.4);
        const bob = idleRock * 0.015 * Math.abs(Math.sin(time * 9)) * (car.kind === 'loco' ? 1 : 0.3);
        return (
          <group key={i} position={t.position} rotation={[0, t.yaw, 0]}>
            <group rotation={[roll, 0, 0]} position={[0, bob, 0]}>
              {car.kind === 'loco' ? (
                <Locomotive wheelDistance={distance} steeringTurn={steeringTurn}>
                  {cab}
                </Locomotive>
              ) : (
                <Wagon color={WAGON_COLORS[car.index]} wheelDistance={distance} glow={glow[car.index] ?? 0}>
                  {riders[car.index]}
                </Wagon>
              )}
            </group>
          </group>
        );
      })}
      {couplers.map((c, i) => (
        <mesh key={i} position={c.mid} quaternion={c.quat} material={couplerMat} castShadow>
          <cylinderGeometry args={[0.07, 0.07, c.len + 0.1, 12]} />
        </mesh>
      ))}
    </group>
  );
};

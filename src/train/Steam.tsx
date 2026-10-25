import React, { useMemo } from 'react';
import * as THREE from 'three';
import { hash, smootherstep } from '../animations/math';
import { LOCO, carLocalToWorld, carTransforms } from './layout';
import type { Track } from './track';

const LIFE = 3.2;

/**
 * Buhar bulutları: bacadan çıkar, yükselir, büyür ve yumuşakça kaybolur.
 * Her bulutun çıkış noktası, çıktığı andaki baca konumudur (tren ilerlerken geride kalır).
 */
export const Steam: React.FC<{
  track: Track;
  time: number;
  emitTimes: number[];
  distanceAt: (sec: number) => number;
}> = ({ track, time, emitTimes, distanceAt }) => {
  // Saydamlık kademeleri (her karede yeni malzeme üretmemek için önceden hazır).
  const mats = useMemo(
    () =>
      Array.from({ length: 49 }, (_, i) => {
        const m = new THREE.MeshStandardMaterial({ color: '#ffffff', roughness: 1, transparent: true, depthWrite: false, emissive: '#ffffff', emissiveIntensity: 0.18 });
        m.opacity = (0.92 * i) / 48;
        return m;
      }),
    [],
  );
  const active = emitTimes.filter((t0) => time >= t0 && time < t0 + LIFE);
  return (
    <group>
      {active.map((t0) => {
        const age = (time - t0) / LIFE;
        const origin = carLocalToWorld(carTransforms(track, distanceAt(t0))[0], LOCO.chimneyTop);
        const seed = Math.round(t0 * 1000);
        const rise = 0.3 + 3.0 * (1 - Math.pow(1 - age, 2));
        const drift = -0.8 * age + (hash(seed) - 0.5) * 0.6 * age;
        const grow = 0.55 + 1.25 * smootherstep(Math.min(1, age * 1.4));
        const fade = 1 - smootherstep((age - 0.45) / 0.55);
        const appear = smootherstep(age / 0.08);
        return (
          <group key={t0} position={[origin.x + drift, origin.y + rise, origin.z + (hash(seed + 1) - 0.5) * 0.4 * age]} scale={grow * appear}>
            {[0, 1, 2, 3].map((k) => {
              const a = (k / 4) * Math.PI * 2 + hash(seed + k);
              const r = k === 0 ? 0 : 0.32;
              const m = mats[Math.round(fade * 48)];
              return (
                <mesh key={k} position={[Math.cos(a) * r, k === 0 ? 0.12 : 0, Math.sin(a) * r]} material={m}>
                  <sphereGeometry args={[k === 0 ? 0.42 : 0.33, 20, 14]} />
                </mesh>
              );
            })}
          </group>
        );
      })}
    </group>
  );
};

import React from 'react';
import * as THREE from 'three';
import { roundedBox, roundedTub } from '../assets/geometry';
import { paint, TRAIN_COLORS as C } from './materials';
import { Wheel } from './Wheel';
import { GAUGE_HALF, RAIL_TOP, WAGON, type WagonColor } from './layout';

const BODY: Record<WagonColor, string> = {
  red: C.red,
  blue: C.blue,
  yellow: C.yellow,
  green: C.green,
  purple: C.purple,
  orange: C.orange,
};

const shade = (hex: string, k: number) => {
  const c = new THREE.Color(hex);
  const hsl = { h: 0, s: 0, l: 0 };
  c.getHSL(hsl);
  c.setHSL(hsl.h, hsl.s, Math.min(1, Math.max(0, hsl.l * k)));
  return `#${c.getHexString()}`;
};

/**
 * Üstü açık renkli vagon. Üzerinde yazı yoktur: çocuklar rengi doğrudan görür.
 * glow: 0..1 — kendi renginde hafif parlama (ani yanıp sönme yok, yalnızca yumuşak geçiş).
 * children → vagona binen karakterler (taban yüksekliği WAGON.floorY).
 */
export const Wagon: React.FC<{
  color: WagonColor;
  wheelDistance: number;
  glow?: number;
  children?: React.ReactNode;
}> = ({ color, wheelDistance, glow = 0, children }) => {
  const base = BODY[color];
  const body = paint(base, { emissive: base, emissiveIntensity: Math.round(glow * 20) / 50 });
  const rim = paint(shade(base, 1.22), { roughness: 0.5 });
  const inner = paint(shade(base, 0.8), { roughness: 0.7 });
  const chassis = paint(C.chassis, { roughness: 0.6 });
  const L = WAGON.length;
  const wy = RAIL_TOP + WAGON.wheelR;
  return (
    <group>
      <mesh position={[0, 0.92, 0]} geometry={roundedBox(L, 0.3, 2.2, 0.2, 0.06)} material={chassis} castShadow receiveShadow />
      {[1, -1].map((side) =>
        [-1.2, 1.2].map((x) => (
          <Wheel key={`${side}${x}`} radius={WAGON.wheelR} angle={wheelDistance / WAGON.wheelR} position={[x, wy, side * GAUGE_HALF]} side={side as 1 | -1} />
        )),
      )}
      {/* gövde (açık kasa) */}
      <mesh position={[0, 1.06, 0]} geometry={roundedTub(L - 0.1, 2.24, 0.62, 0.15, 0.42)} material={body} castShadow receiveShadow />
      <mesh position={[0, 1.12, 0]} geometry={roundedBox(L - 0.3, 0.1, 2.0, 0.3, 0.03)} material={inner} receiveShadow />
      {/* üst kenar şeridi */}
      <mesh position={[0, 1.64, 0]} geometry={roundedTub(L - 0.02, 2.32, 0.12, 0.2, 0.46)} material={rim} castShadow />
      {/* yan süs: yuvarlak düğmeler (yazı yok) */}
      {[1, -1].map((side) =>
        [-1.05, 0, 1.05].map((x) => (
          <mesh key={`${side}${x}`} position={[x, 1.36, side * 1.135]} rotation={[Math.PI / 2, 0, 0]} material={rim}>
            <cylinderGeometry args={[0.16, 0.16, 0.05, 24]} />
          </mesh>
        )),
      )}
      {/* ön/arka bağlantı kancaları */}
      {[1, -1].map((s) => (
        <mesh key={s} position={[s * (L / 2 + 0.05), 0.9, 0]} rotation={[0, 0, Math.PI / 2]} material={paint('#1E1A1C', { roughness: 0.4 })}>
          <cylinderGeometry args={[0.09, 0.09, 0.2, 16]} />
        </mesh>
      ))}
      <group position={[0, WAGON.floorY, 0]}>{children}</group>
    </group>
  );
};

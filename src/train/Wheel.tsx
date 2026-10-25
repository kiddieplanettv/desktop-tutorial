import React from 'react';
import { paint, TRAIN_COLORS } from './materials';

/**
 * Tekerlek. angle = kat edilen mesafe / yarıçap → dönüş her zaman ilerlemeyle uyumludur.
 * Tekerlek yerel Z ekseni etrafında döner (tren +X yönünde ilerler).
 */
export const Wheel: React.FC<{
  radius: number;
  width?: number;
  angle: number;
  position: [number, number, number];
  side: 1 | -1;
}> = ({ radius, width = 0.2, angle, position, side }) => {
  const spokes = 6;
  return (
    <group position={position} rotation={[0, 0, -angle]}>
      {/* lastik/jant */}
      <mesh rotation={[Math.PI / 2, 0, 0]} material={paint(TRAIN_COLORS.wheelRim, { roughness: 0.6 })} castShadow>
        <cylinderGeometry args={[radius, radius, width, 40]} />
      </mesh>
      {/* dış yüz plakası */}
      <mesh position={[0, 0, (side * width) / 2 + side * 0.005]} rotation={[Math.PI / 2, 0, 0]} material={paint('#F4F1EA')}>
        <cylinderGeometry args={[radius * 0.82, radius * 0.82, 0.02, 40]} />
      </mesh>
      {/* jant telleri: dönüşü belirgin kılar */}
      {Array.from({ length: spokes }, (_, i) => (
        <mesh
          key={i}
          position={[0, 0, (side * width) / 2 + side * 0.022]}
          rotation={[0, 0, (i / spokes) * Math.PI * 2]}
          material={paint(TRAIN_COLORS.wheelRim)}
        >
          <boxGeometry args={[radius * 1.5, radius * 0.11, 0.025]} />
        </mesh>
      ))}
      {/* göbek */}
      <mesh position={[0, 0, (side * width) / 2 + side * 0.04]} rotation={[Math.PI / 2, 0, 0]} material={paint(TRAIN_COLORS.wheelHub)}>
        <cylinderGeometry args={[radius * 0.28, radius * 0.3, 0.06, 24]} />
      </mesh>
      {/* jant üzerinde nokta: hız algısı için */}
      <mesh position={[radius * 0.62, 0, (side * width) / 2 + side * 0.03]} rotation={[Math.PI / 2, 0, 0]} material={paint(TRAIN_COLORS.locoOrange)}>
        <cylinderGeometry args={[radius * 0.1, radius * 0.1, 0.03, 16]} />
      </mesh>
    </group>
  );
};

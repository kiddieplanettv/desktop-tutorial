import React, { useMemo } from 'react';
import { grassTexture } from '../assets/proceduralTextures';

/** Pastel yeşil çimen zemini; sahnenin odak noktasının etrafında konumlanır. */
export const Ground: React.FC<{ center: [number, number]; size?: number }> = ({ center, size = 700 }) => {
  const tex = useMemo(() => {
    const t = grassTexture().clone();
    t.needsUpdate = true;
    t.repeat.set(size / 9, size / 9);
    return t;
  }, [size]);
  // doku kaymasın diye merkez doku tekrar aralığına yuvarlanır
  const cx = Math.round(center[0] / 9) * 9;
  const cz = Math.round(center[1] / 9) * 9;
  return (
    <mesh position={[cx, 0, cz]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
      <planeGeometry args={[size, size]} />
      <meshStandardMaterial map={tex} color="#E6FAD8" roughness={1} />
    </mesh>
  );
};

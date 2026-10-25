import React, { useLayoutEffect, useRef } from 'react';
import * as THREE from 'three';

/**
 * Yumuşak gündüz ışığı. Gölge kamerası odak noktasını takip eder,
 * böylece gölgeler sahnenin neresinde olursa olsun keskin ve yumuşak kalır.
 */
export const Lights: React.FC<{ focus: [number, number, number]; shadowSize?: number; sunIntensity?: number }> = ({
  focus,
  shadowSize = 28,
  sunIntensity = 2.1,
}) => {
  const sun = useRef<THREE.DirectionalLight>(null);
  useLayoutEffect(() => {
    const l = sun.current;
    if (!l) return;
    l.position.set(focus[0] + 26, focus[1] + 40, focus[2] + 30);
    l.target.position.set(focus[0], focus[1], focus[2]);
    l.target.updateMatrixWorld();
    const cam = l.shadow.camera as THREE.OrthographicCamera;
    cam.left = -shadowSize;
    cam.right = shadowSize;
    cam.top = shadowSize;
    cam.bottom = -shadowSize;
    cam.near = 1;
    cam.far = 140;
    cam.updateProjectionMatrix();
  });
  return (
    <>
      <hemisphereLight args={['#E4F4FF', '#9CCB7A', 1.15]} />
      <ambientLight intensity={0.18} />
      <directionalLight
        ref={sun}
        color="#FFF2DA"
        intensity={sunIntensity}
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
        shadow-bias={-0.0004}
        shadow-normalBias={0.03}
        shadow-radius={4}
      />
      {/* dolgu ışığı: karakter yüzlerinde sert gölge kalmasın */}
      <directionalLight color="#DDEBFF" intensity={0.45} position={[focus[0] - 20, focus[1] + 12, focus[2] + 25]} />
    </>
  );
};

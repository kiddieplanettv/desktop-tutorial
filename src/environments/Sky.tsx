import React, { useMemo } from 'react';
import * as THREE from 'three';

/** Mavi gökyüzü kubbesi: tepede canlı mavi, ufukta açık pastel. */
export const Sky: React.FC<{ center: [number, number, number]; top?: string; horizon?: string; bottom?: string }> = ({
  center,
  top = '#4FB4F5',
  horizon = '#D6F1FF',
  bottom = '#EAF8FF',
}) => {
  const mat = useMemo(
    () =>
      new THREE.ShaderMaterial({
        side: THREE.BackSide,
        depthWrite: false,
        fog: false,
        uniforms: {
          top: { value: new THREE.Color(top) },
          horizon: { value: new THREE.Color(horizon) },
          bottom: { value: new THREE.Color(bottom) },
        },
        vertexShader: /* glsl */ `
          varying vec3 vDir;
          void main() {
            vDir = normalize(position);
            vec4 p = modelViewMatrix * vec4(position, 1.0);
            gl_Position = projectionMatrix * p;
          }`,
        fragmentShader: /* glsl */ `
          uniform vec3 top; uniform vec3 horizon; uniform vec3 bottom;
          varying vec3 vDir;
          void main() {
            float h = vDir.y;
            vec3 c = h > 0.0 ? mix(horizon, top, pow(smoothstep(0.0, 0.75, h), 0.8)) : mix(horizon, bottom, smoothstep(0.0, -0.2, h));
            gl_FragColor = vec4(c, 1.0);
            #include <colorspace_fragment>
          }`,
      }),
    [top, horizon, bottom],
  );
  return (
    <mesh position={center} material={mat} renderOrder={-10} frustumCulled={false}>
      <sphereGeometry args={[900, 32, 16]} />
    </mesh>
  );
};

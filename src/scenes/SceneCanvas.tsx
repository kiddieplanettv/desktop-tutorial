import React, { useLayoutEffect } from 'react';
import * as THREE from 'three';
import { useThree } from '@react-three/fiber';
import { ThreeCanvas } from '@remotion/three';
import { useVideoConfig } from 'remotion';
import { Sky } from '../environments/Sky';
import { Lights } from '../environments/Lights';

export interface CameraShot {
  position: [number, number, number];
  target: [number, number, number];
  fov: number;
}

/** Kamerayı her karede verilen konuma/hedefe yerleştirir (kareye bağlı, deterministik). */
const CameraRig: React.FC<CameraShot> = ({ position, target, fov }) => {
  const camera = useThree((s) => s.camera) as THREE.PerspectiveCamera;
  useLayoutEffect(() => {
    camera.position.set(...position);
    camera.fov = fov;
    camera.near = 0.1;
    camera.far = 2000;
    camera.lookAt(...target);
    camera.updateProjectionMatrix();
  });
  return null;
};

/**
 * Tüm sahnelerin ortak 3B tuvali: gökyüzü, ışık, sis, kamera.
 * Her sahne bağımsızdır; sadece kendi içeriğini bu tuvale koyar.
 */
export const SceneCanvas: React.FC<{
  camera: CameraShot;
  /** Gölge odak noktası (genelde aksiyonun merkezi). */
  focus: [number, number, number];
  fog?: [string, number, number];
  children: React.ReactNode;
}> = ({ camera, focus, fog = ['#D6F1FF', 90, 380], children }) => {
  const { width, height } = useVideoConfig();
  return (
    <ThreeCanvas
      width={width}
      height={height}
      shadows
      dpr={1}
      gl={{ antialias: true, powerPreference: 'high-performance' }}
      camera={{ fov: camera.fov, position: camera.position, near: 0.1, far: 2000 }}
      onCreated={({ gl }) => {
        gl.toneMapping = THREE.NeutralToneMapping;
        gl.toneMappingExposure = 1.0;
        gl.shadowMap.type = THREE.PCFShadowMap;
      }}
      style={{ backgroundColor: '#BFE6FF' }}
    >
      <CameraRig {...camera} />
      <fog attach="fog" args={fog} />
      <Sky center={camera.position} />
      <Lights focus={focus} />
      {children}
    </ThreeCanvas>
  );
};

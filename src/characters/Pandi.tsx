import React, { useLayoutEffect, useMemo } from 'react';
import * as THREE from 'three';
import { furBumpTexture, makeCanvas, strandNoiseTexture } from '../assets/proceduralTextures';
import {
  FACE,
  FACE_PATCH,
  bodyColorTexture,
  drawFace,
  eyeTexture,
  headColorTexture,
  headNormal,
  headPoint,
  makeHeadGeometry,
} from './pandiHead';
import { NEUTRAL_POSE, type PandiPose, type ArmPose } from './pose';

/**
 * PANDİ — Kiddie TV ana karakteri.
 * Referans: src/assets/reference/pandi-referans.jpg
 * Ölçek: ayakta boy ≈ 2.25 birim (kulaklar dahil). Kök noktası ayakların altındadır.
 * Yerel +Z = Pandi'nin baktığı yön.
 */

const COLORS = {
  white: '#fbf8f4',
  black: '#262224',
  nose: '#151214',
  pawPad: '#4a3f44',
} as const;

const FUR_SHELLS = 4;
const SHELL_STEP = 0.007;

// Paylaşılan geometri ve malzemeler (tüm Pandi örnekleri aynı görünür).
const useAssets = () =>
  useMemo(() => {
    const headTex = headColorTexture();
    const bump = furBumpTexture();
    const strands = strandNoiseTexture().clone();
    strands.needsUpdate = true;
    strands.repeat.set(40, 20);

    const headGeo = makeHeadGeometry(1);
    const shellGeos = Array.from({ length: FUR_SHELLS }, (_, i) => makeHeadGeometry(1 + (i + 1) * SHELL_STEP, 64, 40));

    const headBump = bump.clone();
    headBump.needsUpdate = true;
    headBump.repeat.set(6, 3);

    const headMat = new THREE.MeshPhysicalMaterial({
      map: headTex,
      roughness: 0.88,
      sheen: 0.35,
      sheenRoughness: 0.5,
      sheenColor: new THREE.Color('#ffffff'),
      bumpMap: headBump,
      bumpScale: 0.5,
      emissive: new THREE.Color('#ffffff'),
      emissiveMap: headTex,
      emissiveIntensity: 0.12,
    });
    const shellMats = Array.from({ length: FUR_SHELLS }, (_, i) =>
      new THREE.MeshStandardMaterial({
        map: headTex,
        alphaMap: strands,
        alphaTest: 0.5 + i * 0.12,
        roughness: 1,
        emissive: new THREE.Color('#ffffff'),
        emissiveMap: headTex,
        emissiveIntensity: 0.12,
      }),
    );

    const bodyTex = bodyColorTexture();
    const bodyBump = bump.clone();
    bodyBump.needsUpdate = true;
    bodyBump.repeat.set(3, 2);
    const bodyMat = new THREE.MeshPhysicalMaterial({
      map: bodyTex,
      roughness: 0.88,
      sheen: 0.35,
      sheenRoughness: 0.5,
      sheenColor: new THREE.Color('#ffffff'),
      bumpMap: bodyBump,
      bumpScale: 0.5,
      emissive: new THREE.Color('#ffffff'),
      emissiveMap: bodyTex,
      emissiveIntensity: 0.12,
    });
    const blackBump = bump.clone();
    blackBump.needsUpdate = true;
    blackBump.repeat.set(2, 2);
    const blackMat = new THREE.MeshPhysicalMaterial({
      color: COLORS.black,
      roughness: 0.85,
      sheen: 1,
      sheenRoughness: 0.5,
      sheenColor: new THREE.Color('#8a8088'),
      bumpMap: blackBump,
      bumpScale: 1.5,
    });
    const whiteFurMat = new THREE.MeshPhysicalMaterial({
      color: COLORS.white,
      roughness: 0.88,
      sheen: 0.35,
      sheenRoughness: 0.5,
      sheenColor: new THREE.Color('#ffffff'),
      emissive: new THREE.Color('#ffffff'),
      emissiveIntensity: 0.12,
    });
    const eyeMat = new THREE.MeshPhysicalMaterial({
      map: eyeTexture(),
      roughness: 0.18,
      clearcoat: 1,
      clearcoatRoughness: 0.08,
    });
    const highlightMat = new THREE.MeshBasicMaterial({ color: '#ffffff', toneMapped: false });
    const noseMat = new THREE.MeshPhysicalMaterial({ color: COLORS.nose, roughness: 0.3, clearcoat: 0.8 });
    const padMat = new THREE.MeshStandardMaterial({ color: COLORS.pawPad, roughness: 0.7 });

    // Hareketli yüz katmanı (ağız + kaşlar)
    const { c: faceCanvas, ctx: faceCtx } = makeCanvas(1024, 1024);
    const faceTex = new THREE.CanvasTexture(faceCanvas);
    faceTex.colorSpace = THREE.SRGBColorSpace;
    faceTex.anisotropy = 8;
    const { l0, l1, p0, p1 } = FACE_PATCH;
    const faceGeo = makeHeadGeometry(
      1 + (FUR_SHELLS + 1.5) * SHELL_STEP,
      48,
      48,
      Math.PI / 2 + l0,
      l1 - l0,
      Math.PI / 2 - p1,
      p1 - p0,
    );
    const faceMat = new THREE.MeshStandardMaterial({
      map: faceTex,
      transparent: true,
      roughness: 0.8,
      depthWrite: false,
      polygonOffset: true,
      polygonOffsetFactor: -2,
    });

    return {
      headGeo,
      shellGeos,
      headMat,
      shellMats,
      bodyMat,
      blackMat,
      whiteFurMat,
      eyeMat,
      highlightMat,
      noseMat,
      padMat,
      faceGeo,
      faceMat,
      faceTex,
      faceCtx,
    };
  }, []);

type Assets = ReturnType<typeof useAssets>;

const surfaceQuat = (n: THREE.Vector3, from = new THREE.Vector3(0, 0, 1)) =>
  new THREE.Quaternion().setFromUnitVectors(from, n);

const EYE_R = 0.118;
const EYE_DEPTH = EYE_R * 0.5;
const EYE_TALL = EYE_R * 1.12;
/** Göz yüzeyindeki (x, y) noktasının hemen önü — parlamalar göze yapışık durur. */
const onEye = (x: number, y: number): [number, number, number] => [
  x,
  y,
  EYE_DEPTH * Math.sqrt(Math.max(0, 1 - (x / EYE_R) ** 2 - (y / EYE_TALL) ** 2)) + 0.004,
];

const Eye: React.FC<{ side: 1 | -1; blink: number; surprise: number; a: Assets }> = ({ side, blink, surprise, a }) => {
  const { pos, quat } = useMemo(() => {
    const l = side * FACE.eye.lambda;
    const n = headNormal(l, FACE.eye.phi);
    const p = headPoint(l, FACE.eye.phi).addScaledVector(n, 0.012);
    return { pos: p, quat: surfaceQuat(n) };
  }, [side]);
  const grow = 1 + surprise * 0.14;
  const squash = Math.max(0.06, 1 - blink);
  // Parlama noktaları her iki gözde de aynı yönde (sol üst) — referanstaki ışık gibi.
  return (
    <group position={pos} scale={[grow, grow * squash, grow]}>
      <group quaternion={quat}>
        <mesh rotation={[Math.PI / 2, 0, 0]} scale={[EYE_R, EYE_DEPTH, EYE_TALL]} material={a.eyeMat}>
          <sphereGeometry args={[1, 40, 24]} />
        </mesh>
        {blink < 0.6 && (
          <>
            <mesh position={onEye(-0.04, 0.045)} scale={[0.036, 0.042, 0.01]} material={a.highlightMat}>
              <sphereGeometry args={[1, 16, 12]} />
            </mesh>
            <mesh position={onEye(0.038, -0.045)} scale={[0.018, 0.018, 0.006]} material={a.highlightMat}>
              <sphereGeometry args={[1, 12, 10]} />
            </mesh>
          </>
        )}
      </group>
    </group>
  );
};

const Ear: React.FC<{ side: 1 | -1; a: Assets }> = ({ side, a }) => {
  const { pos, quat } = useMemo(() => {
    const l = side * FACE.ear.lambda;
    const n = headNormal(l, FACE.ear.phi);
    const p = headPoint(l, FACE.ear.phi).addScaledVector(n, 0.06);
    return { pos: p, quat: surfaceQuat(n) };
  }, [side]);
  return (
    <mesh position={pos} quaternion={quat} scale={[0.235, 0.225, 0.13]} material={a.blackMat} castShadow>
      <sphereGeometry args={[1, 32, 20]} />
    </mesh>
  );
};

const Tuft: React.FC<{ a: Assets }> = ({ a }) => {
  const top = useMemo(() => headPoint(0, 1.25), []);
  // Başın üstünde kıvrık, yumuşak beyaz tüy tutamı (referanstaki gibi).
  const wisps: [number, number, number, number, number][] = [
    // x, y, z, eğim (z ekseni), boy
    [-0.06, 0.07, 0.0, 0.5, 0.75],
    [0.0, 0.1, 0.02, -0.15, 1.0],
    [0.065, 0.065, 0.0, -0.65, 0.7],
  ];
  return (
    <group position={top} rotation={[-0.25, 0, 0]}>
      {wisps.map(([x, y, z, rz, h], i) => (
        <mesh key={i} position={[x, y * h, z]} rotation={[0.2, 0, rz]} scale={[0.05, 0.13 * h, 0.045]} material={a.whiteFurMat} castShadow>
          <sphereGeometry args={[1, 14, 12]} />
        </mesh>
      ))}
    </group>
  );
};

const Nose: React.FC<{ a: Assets }> = ({ a }) => {
  const { pos, quat } = useMemo(() => {
    const n = headNormal(0, FACE.nose.phi);
    return { pos: headPoint(0, FACE.nose.phi).addScaledVector(n, 0.03), quat: surfaceQuat(n) };
  }, []);
  return (
    <group position={pos} quaternion={quat}>
      <mesh scale={[0.085, 0.06, 0.05]} material={a.noseMat} castShadow>
        <sphereGeometry args={[1, 28, 18]} />
      </mesh>
      <mesh position={[-0.02, 0.025, 0.043]} scale={[0.022, 0.012, 0.006]} material={a.highlightMat}>
        <sphereGeometry args={[1, 10, 8]} />
      </mesh>
    </group>
  );
};

const Head: React.FC<{ pose: PandiPose; a: Assets }> = ({ pose, a }) => {
  // Ağız/kaş katmanını yalnızca değerler değişince yeniden çiz.
  const q = (v: number) => Math.round(v * 100) / 100;
  const key = `${q(pose.smile)}|${q(pose.mouthOpen)}|${q(pose.surprise)}|${q(pose.browRaise)}`;
  useLayoutEffect(() => {
    drawFace(a.faceCtx, 1024, 1024, {
      smile: pose.smile,
      mouthOpen: pose.mouthOpen,
      surprise: pose.surprise,
      browRaise: pose.browRaise,
    });
    a.faceTex.needsUpdate = true;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, a]);

  return (
    <group>
      <mesh geometry={a.headGeo} material={a.headMat} castShadow receiveShadow />
      {a.shellGeos.map((g, i) => (
        <mesh key={i} geometry={g} material={a.shellMats[i]} />
      ))}
      <mesh geometry={a.faceGeo} material={a.faceMat} renderOrder={2} />
      <Eye side={1} blink={pose.blink} surprise={pose.surprise} a={a} />
      <Eye side={-1} blink={pose.blink} surprise={pose.surprise} a={a} />
      <Nose a={a} />
      <Ear side={1} a={a} />
      <Ear side={-1} a={a} />
      <Tuft a={a} />
    </group>
  );
};

const Arm: React.FC<{ side: 1 | -1; arm: ArmPose; a: Assets }> = ({ side, arm, a }) => (
  <group position={[side * 0.33, 0.47, 0.04]} rotation={[-arm.forward, 0, side * arm.raise]}>
    <mesh position={[0, -0.22, 0]} material={a.blackMat} castShadow>
      <capsuleGeometry args={[0.135, 0.3, 8, 20]} />
    </mesh>
    <group position={[0, -0.46, 0]} rotation={[0, arm.twist, 0]}>
      <mesh scale={[1, 0.95, 1]} material={a.blackMat} castShadow>
        <sphereGeometry args={[0.158, 24, 18]} />
      </mesh>
      <mesh position={[0, -0.06, 0.11]} scale={[0.07, 0.05, 0.03]} material={a.padMat}>
        <sphereGeometry args={[1, 12, 10]} />
      </mesh>
    </group>
  </group>
);

const Leg: React.FC<{ side: 1 | -1; swing: number; a: Assets }> = ({ side, swing, a }) => (
  <group position={[side * 0.19, 0.4, 0]} rotation={[-swing, 0, 0]}>
    <mesh position={[0, -0.17, 0]} material={a.blackMat} castShadow>
      <capsuleGeometry args={[0.16, 0.14, 8, 20]} />
    </mesh>
    <mesh position={[0, -0.3, 0.06]} scale={[1, 0.7, 1.25]} material={a.blackMat} castShadow>
      <sphereGeometry args={[0.16, 20, 14]} />
    </mesh>
  </group>
);

export interface PandiProps {
  pose?: PandiPose;
  position?: [number, number, number];
  rotation?: [number, number, number];
  scale?: number;
}

export const Pandi: React.FC<PandiProps> = ({ pose = NEUTRAL_POSE, position, rotation, scale = 1 }) => {
  const a = useAssets();
  const sq = pose.squash;
  const sitLeg = pose.sit * 1.45;
  return (
    <group position={position} rotation={rotation} scale={scale}>
      <group rotation={[0, pose.bodyYaw, 0]} position={[0, pose.lift, 0]} scale={[1 - sq * 0.45, 1 + sq, 1 - sq * 0.45]}>
        <Leg side={1} swing={pose.legL + sitLeg} a={a} />
        <Leg side={-1} swing={pose.legR + sitLeg} a={a} />
        {/* gövde: kalçadan döner */}
        <group position={[0, 0.4, 0]} rotation={[pose.bodyPitch, 0, pose.bodyRoll]}>
          <mesh position={[0, 0.24, 0]} scale={[0.4, 0.42, 0.36]} rotation={[0, -Math.PI / 2, 0]} material={a.bodyMat} castShadow receiveShadow>
            <sphereGeometry args={[1, 40, 28]} />
          </mesh>
          <Arm side={1} arm={pose.armL} a={a} />
          <Arm side={-1} arm={pose.armR} a={a} />
          {/* boyun ve kafa */}
          <group position={[0, 0.55, 0.02]} rotation={[pose.headPitch, pose.headYaw, pose.headRoll, 'YXZ']}>
            <group position={[0, 0.5, 0.03]}>
              <Head pose={pose} a={a} />
            </group>
          </group>
        </group>
      </group>
    </group>
  );
};

/** Ayakta yükseklik ve kafa merkezi (kamera hedeflemesi için). */
export const PANDI_METRICS = {
  height: 2.2,
  headCenterY: 1.45,
  shoulderY: 0.87,
  hipY: 0.4,
} as const;

import React, { useLayoutEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { hash } from '../animations/math';
import { wind } from './wind';
import { paint } from '../train/materials';

/** Yuvarlak taçlı oyuncak ağaç; rüzgârla hafifçe sallanır. */
export const Tree: React.FC<{
  position: [number, number, number];
  scale?: number;
  time: number;
  crown?: string;
  seed?: number;
  fruit?: { color: string; count: number; size?: number };
}> = ({ position, scale = 1, time, crown = '#5CC85A', seed = 1, fruit }) => {
  const sway = wind(time, position[0], position[2]);
  const blobs = useMemo(
    () =>
      [
        [0, 0, 0, 1.25],
        [0.85, -0.25, 0.2, 0.85],
        [-0.8, -0.2, -0.1, 0.9],
        [0.1, 0.55, -0.25, 0.85],
        [-0.15, -0.35, 0.75, 0.75],
      ].map(([x, y, z, r], i) => [x + (hash(seed + i) - 0.5) * 0.3, y, z, r * (0.9 + hash(seed * 7 + i) * 0.2)] as const),
    [seed],
  );
  const fruits = useMemo(() => {
    if (!fruit) return [];
    return Array.from({ length: fruit.count }, (_, i) => {
      const a = hash(seed * 13 + i) * Math.PI * 2;
      const y = (hash(seed * 17 + i) - 0.35) * 1.4;
      const r = Math.sqrt(Math.max(0.2, 1.5 * 1.5 - y * y)) * 0.98;
      return [Math.cos(a) * r, y, Math.sin(a) * r] as const;
    });
  }, [fruit, seed]);
  const crownMat = paint(crown, { roughness: 0.85 });
  return (
    <group position={position} scale={scale}>
      <mesh position={[0, 1.0, 0]} material={paint('#9A6A43', { roughness: 0.9 })} castShadow>
        <cylinderGeometry args={[0.2, 0.3, 2.0, 14]} />
      </mesh>
      <group position={[0, 2.0, 0]} rotation={[sway * 0.6, 0, sway]}>
        <group position={[0, 1.1, 0]}>
          {blobs.map(([x, y, z, r], i) => (
            <mesh key={i} position={[x, y, z]} material={crownMat} castShadow receiveShadow>
              <sphereGeometry args={[r, 28, 20]} />
            </mesh>
          ))}
          {fruits.map((p, i) => (
            <group key={i} position={p as unknown as [number, number, number]}>
              <mesh material={paint(fruit!.color, { roughness: 0.4 })} castShadow>
                <sphereGeometry args={[fruit!.size ?? 0.22, 18, 14]} />
              </mesh>
              <mesh position={[0, (fruit!.size ?? 0.22) * 1.05, 0]} material={paint('#6B4A2E')}>
                <cylinderGeometry args={[0.025, 0.025, 0.12, 6]} />
              </mesh>
            </group>
          ))}
        </group>
      </group>
    </group>
  );
};

export interface FlowerSpec {
  x: number;
  z: number;
  color: string;
  scale?: number;
}

/**
 * Çiçek tarlası (instanced — yüzlerce çiçek tek çizim çağrısıyla).
 * Her çiçek: sap, 5 yaprak, sarı/beyaz göbek. Rüzgârla sallanır.
 */
export const Flowers: React.FC<{ items: FlowerSpec[]; time: number; windStrength?: number }> = ({ items, time, windStrength = 1 }) => {
  const stems = useRef<THREE.InstancedMesh>(null);
  const petals = useRef<THREE.InstancedMesh>(null);
  const centers = useRef<THREE.InstancedMesh>(null);
  const n = items.length;
  const geo = useMemo(() => {
    const petal = new THREE.SphereGeometry(1, 12, 8);
    petal.scale(0.13, 0.05, 0.085);
    petal.translate(0.13, 0, 0);
    const stem = new THREE.CylinderGeometry(0.025, 0.03, 0.55, 5);
    stem.translate(0, 0.275, 0);
    return { petal, stem };
  }, []);

  useLayoutEffect(() => {
    const o = new THREE.Object3D();
    const head = new THREE.Object3D();
    const c = new THREE.Color();
    items.forEach((f, i) => {
      const s = f.scale ?? 1;
      const sway = wind(time, f.x, f.z, windStrength) * 2.2;
      const h = 0.55 * s;
      o.position.set(f.x, 0, f.z);
      o.rotation.set(sway * 0.5, 0, sway);
      o.scale.set(s, s, s);
      o.updateMatrix();
      stems.current?.setMatrixAt(i, o.matrix);
      // çiçek başı: sapın ucu
      const tip = new THREE.Vector3(0, h, 0).applyEuler(o.rotation);
      head.position.set(f.x + tip.x, tip.y, f.z + tip.z);
      head.rotation.set(sway * 0.5 - 0.25, hash(i) * 6.28, sway);
      head.scale.set(s, s, s);
      head.updateMatrix();
      centers.current?.setMatrixAt(i, head.matrix);
      for (let k = 0; k < 5; k++) {
        const p = new THREE.Object3D();
        p.rotation.y = (k / 5) * Math.PI * 2;
        p.updateMatrix();
        const m = head.matrix.clone().multiply(p.matrix);
        petals.current?.setMatrixAt(i * 5 + k, m);
        petals.current?.setColorAt(i * 5 + k, c.set(f.color));
      }
    });
    for (const r of [stems, petals, centers]) {
      if (r.current) {
        r.current.instanceMatrix.needsUpdate = true;
        if (r.current.instanceColor) r.current.instanceColor.needsUpdate = true;
        r.current.computeBoundingSphere();
      }
    }
  });

  if (n === 0) return null;
  return (
    <group>
      <instancedMesh ref={stems} args={[geo.stem, undefined, n]} castShadow>
        <meshStandardMaterial color="#4DAF4A" roughness={0.9} />
      </instancedMesh>
      <instancedMesh ref={petals} args={[geo.petal, undefined, n * 5]} castShadow>
        <meshStandardMaterial roughness={0.75} />
      </instancedMesh>
      <instancedMesh ref={centers} args={[undefined, undefined, n]}>
        <sphereGeometry args={[0.075, 10, 8]} />
        <meshStandardMaterial color="#FFE07A" roughness={0.7} />
      </instancedMesh>
    </group>
  );
};

/** Yumuşak beyaz bulut: yavaşça sürüklenir. */
export const Cloud: React.FC<{ position: [number, number, number]; scale?: number; time: number; speed?: number; seed?: number }> = ({
  position,
  scale = 1,
  time,
  speed = 0.6,
  seed = 1,
}) => {
  const puffs = useMemo(
    () =>
      Array.from({ length: 6 }, (_, i) => {
        const x = (i - 2.5) * 1.5 + (hash(seed + i) - 0.5);
        const y = Math.sin((i / 5) * Math.PI) * 0.9 + hash(seed * 3 + i) * 0.4;
        const r = 1.2 + Math.sin((i / 5) * Math.PI) * 0.9 + hash(seed * 5 + i) * 0.3;
        return [x, y, (hash(seed * 9 + i) - 0.5) * 1.2, r] as const;
      }),
    [seed],
  );
  const mat = useMemo(
    () => new THREE.MeshStandardMaterial({ color: '#FFFFFF', roughness: 1, emissive: '#FFFFFF', emissiveIntensity: 0.25 }),
    [],
  );
  return (
    <group position={[position[0] + time * speed, position[1], position[2]]} scale={scale}>
      {puffs.map(([x, y, z, r], i) => (
        <mesh key={i} position={[x, y, z]} material={mat}>
          <sphereGeometry args={[r, 24, 16]} />
        </mesh>
      ))}
      <mesh position={[0, -0.4, 0]} scale={[5.2, 0.9, 1.6]} material={mat}>
        <sphereGeometry args={[1, 24, 16]} />
      </mesh>
    </group>
  );
};

/** Yuvarlak pastel tepe. */
export const Hill: React.FC<{ position: [number, number, number]; radius: number; height: number; color?: string }> = ({
  position,
  radius,
  height,
  color = '#8FD873',
}) => (
  <mesh position={position} scale={[radius, height, radius * 0.8]} receiveShadow>
    <sphereGeometry args={[1, 48, 24, 0, Math.PI * 2, 0, Math.PI / 2]} />
    <meshStandardMaterial color={color} roughness={1} />
  </mesh>
);

/** Küçük sevimli ev. */
export const House: React.FC<{ position: [number, number, number]; rotationY?: number; wall?: string; roof?: string; scale?: number }> = ({
  position,
  rotationY = 0,
  wall = '#FFF3D6',
  roof = '#F0614E',
  scale = 1,
}) => (
  <group position={position} rotation={[0, rotationY, 0]} scale={scale}>
    <mesh position={[0, 1.1, 0]} material={paint(wall, { roughness: 0.85 })} castShadow receiveShadow>
      <boxGeometry args={[2.8, 2.2, 2.4]} />
    </mesh>
    <mesh position={[0, 2.95, 0]} rotation={[0, Math.PI / 4, 0]} material={paint(roof, { roughness: 0.7 })} castShadow>
      <coneGeometry args={[2.25, 1.5, 4, 1]} />
    </mesh>
    <mesh position={[0, 0.65, 1.21]} material={paint('#B9774A')}>
      <boxGeometry args={[0.7, 1.3, 0.05]} />
    </mesh>
    <mesh position={[0.18, 0.65, 1.25]} material={paint('#FFD25A')}>
      <sphereGeometry args={[0.06, 10, 8]} />
    </mesh>
    {[-0.9, 0.9].map((x) => (
      <group key={x} position={[x, 1.35, 1.21]}>
        <mesh material={paint('#FFFFFF')}>
          <boxGeometry args={[0.66, 0.66, 0.05]} />
        </mesh>
        <mesh position={[0, 0, 0.02]} material={paint('#9ED8FF', { roughness: 0.2 })}>
          <boxGeometry args={[0.52, 0.52, 0.05]} />
        </mesh>
      </group>
    ))}
    <mesh position={[0.8, 3.2, -0.3]} material={paint('#C0573F')} castShadow>
      <boxGeometry args={[0.35, 0.8, 0.35]} />
    </mesh>
  </group>
);

/** Basit çalı. */
export const Bush: React.FC<{ position: [number, number, number]; scale?: number; color?: string }> = ({ position, scale = 1, color = '#58C25A' }) => (
  <group position={position} scale={scale}>
    {[
      [0, 0.35, 0, 0.55],
      [0.5, 0.28, 0.1, 0.42],
      [-0.48, 0.3, -0.05, 0.45],
    ].map(([x, y, z, r], i) => (
      <mesh key={i} position={[x, y, z]} material={paint(color, { roughness: 0.9 })} castShadow receiveShadow>
        <sphereGeometry args={[r, 20, 14]} />
      </mesh>
    ))}
  </group>
);

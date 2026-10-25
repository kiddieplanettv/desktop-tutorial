import React, { useLayoutEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import type { Track } from '../train/track';
import { GAUGE_HALF } from '../train/layout';

/**
 * Raylar, traversler ve balast şeridi. Yalnızca [from, to] mesafe aralığı çizilir
 * (her sahne kendi bölümünü çizer; performans için).
 */
export const Rails: React.FC<{ track: Track; from: number; to: number }> = ({ track, from, to }) => {
  const s0 = Math.max(0, from);
  const s1 = Math.min(track.length, to);
  const sleeperGap = 0.95;
  const count = Math.max(0, Math.floor((s1 - s0) / sleeperGap));

  const { railGeos, ballastGeo } = useMemo(() => {
    const step = 1.0;
    const n = Math.max(2, Math.ceil((s1 - s0) / step));
    const left: THREE.Vector3[] = [];
    const right: THREE.Vector3[] = [];
    for (let i = 0; i <= n; i++) {
      const s = s0 + ((s1 - s0) * i) / n;
      left.push(track.offsetPoint(s, GAUGE_HALF, 0.1));
      right.push(track.offsetPoint(s, -GAUGE_HALF, 0.1));
    }
    const railGeos = [left, right].map(
      (pts) => new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), n * 2, 0.075, 8, false),
    );
    // balast: düz şerit
    const pos: number[] = [];
    const idx: number[] = [];
    const half = GAUGE_HALF + 0.75;
    for (let i = 0; i <= n; i++) {
      const s = s0 + ((s1 - s0) * i) / n;
      const a = track.offsetPoint(s, half, 0.025);
      const b = track.offsetPoint(s, -half, 0.025);
      pos.push(a.x, a.y, a.z, b.x, b.y, b.z);
      if (i < n) {
        const k = i * 2;
        idx.push(k, k + 2, k + 1, k + 1, k + 2, k + 3);
      }
    }
    const ballastGeo = new THREE.BufferGeometry();
    ballastGeo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    ballastGeo.setIndex(idx);
    ballastGeo.computeVertexNormals();
    return { railGeos, ballastGeo };
  }, [track, s0, s1]);

  const sleepers = useRef<THREE.InstancedMesh>(null);
  useLayoutEffect(() => {
    const m = sleepers.current;
    if (!m) return;
    const o = new THREE.Object3D();
    for (let i = 0; i < count; i++) {
      const f = track.frame(s0 + i * sleeperGap);
      o.position.copy(f.position).setY(0.05);
      o.rotation.set(0, f.yaw, 0);
      o.updateMatrix();
      m.setMatrixAt(i, o.matrix);
    }
    m.instanceMatrix.needsUpdate = true;
    m.computeBoundingSphere();
  }, [track, s0, count]);

  return (
    <group>
      <mesh geometry={ballastGeo} receiveShadow>
        <meshStandardMaterial color="#D9CBB0" roughness={1} side={THREE.DoubleSide} />
      </mesh>
      <instancedMesh ref={sleepers} args={[undefined, undefined, Math.max(1, count)]} receiveShadow castShadow>
        <boxGeometry args={[0.38, 0.1, GAUGE_HALF * 2 + 0.7]} />
        <meshStandardMaterial color="#A86E43" roughness={0.85} />
      </instancedMesh>
      {railGeos.map((g, i) => (
        <mesh key={i} geometry={g} castShadow receiveShadow>
          <meshStandardMaterial color="#8E97A8" roughness={0.35} metalness={0.4} />
        </mesh>
      ))}
    </group>
  );
};

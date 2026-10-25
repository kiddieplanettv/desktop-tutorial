import React from 'react';
import { roundedBox } from '../assets/geometry';
import { paint } from '../train/materials';

const BUNTING = ['#E8332F', '#2F7BEA', '#FFD21F', '#35B84A', '#8E4FD8', '#FF8A1F'];

/**
 * Renkli küçük tren istasyonu (peron, saçak, bank, lambalar, süs bayrakları).
 * Peron rayın +Z tarafında, x ∈ [x0, x1] arasında uzanır. Yazı/marka içermez.
 */
export const Station: React.FC<{
  x0: number;
  x1: number;
  time: number;
  canopyFrom: number;
  canopyTo: number;
  roof?: string;
  posts?: string;
  /** Lamba x konumları (kamera görüşünü kapatmayacak yerlere). */
  lamps?: number[];
  /** Bu x aralığına saksı konmaz (ön plan boş kalsın). */
  keepClear?: [number, number];
  /** İstasyon binasının konumu (rayın karşı tarafında). */
  building?: [number, number, number];
}> = ({ x0, x1, time, canopyFrom, canopyTo, roof = '#FF7A59', posts = '#FFFFFF', lamps = [x0 + 2.5], keepClear, building }) => {
  const len = x1 - x0;
  const cx = (x0 + x1) / 2;
  const edgeZ = 1.65;
  const depth = 5.0;
  const pz = edgeZ + depth / 2;
  const platH = 0.9;
  const cLen = canopyTo - canopyFrom;
  const cCx = (canopyFrom + canopyTo) / 2;
  const roofY = 4.7;
  const postCount = Math.max(2, Math.round(cLen / 4) + 1);
  return (
    <group>
      {/* peron */}
      <mesh position={[cx, platH / 2, pz]} geometry={roundedBox(len, platH, depth, 0.3, 0.08)} material={paint('#F2E3C6', { roughness: 0.9 })} castShadow receiveShadow />
      {/* kenar şeridi */}
      <mesh position={[cx, platH + 0.005, edgeZ + 0.28]} material={paint('#FFD21F', { roughness: 0.8 })} receiveShadow>
        <boxGeometry args={[len - 0.3, 0.02, 0.3]} />
      </mesh>
      {/* karo çizgileri */}
      {Array.from({ length: Math.floor(len / 2) }, (_, i) => (
        <mesh key={i} position={[x0 + 1 + i * 2, platH + 0.004, pz + 0.3]} material={paint('#E6D3AF')}>
          <boxGeometry args={[0.05, 0.01, depth - 1.2]} />
        </mesh>
      ))}

      {/* saçak dikmeleri ve çatı */}
      {Array.from({ length: postCount }, (_, i) => {
        const x = canopyFrom + 0.4 + ((cLen - 0.8) * i) / (postCount - 1);
        return [edgeZ + 1.0, edgeZ + depth - 0.6].map((z) => (
          <mesh key={`${i}-${z}`} position={[x, platH + (roofY - platH) / 2, z]} material={paint(posts)} castShadow>
            <cylinderGeometry args={[0.12, 0.14, roofY - platH, 16]} />
          </mesh>
        ));
      })}
      <mesh position={[cCx, roofY + 0.12, pz]} geometry={roundedBox(cLen + 0.8, 0.3, depth + 0.6, 0.4, 0.1)} material={paint(roof)} castShadow receiveShadow />
      {/* çizgili saçak kenarı */}
      {Array.from({ length: Math.floor((cLen + 0.6) / 0.7) }, (_, i) => (
        <mesh
          key={i}
          position={[canopyFrom - 0.3 + 0.35 + i * 0.7, roofY - 0.12, edgeZ + 0.72]}
          material={paint(i % 2 ? '#FFFFFF' : roof)}
          castShadow
        >
          <cylinderGeometry args={[0.35, 0.35, 0.18, 18, 1, false, Math.PI / 2, Math.PI]} />
        </mesh>
      ))}
      {/* süs bayrakları: rüzgârda hafifçe dalgalanır */}
      {Array.from({ length: Math.floor(cLen / 0.8) }, (_, i) => {
        const x = canopyFrom + 0.4 + i * 0.8;
        const sag = Math.sin((i / Math.max(1, Math.floor(cLen / 0.8) - 1)) * Math.PI) * 0.0;
        const flutter = Math.sin(time * 2.2 + i * 0.7) * 0.18;
        return (
          <mesh
            key={i}
            position={[x, roofY - 0.55 - sag, edgeZ + 0.62]}
            rotation={[flutter, 0, Math.PI]}
            material={paint(BUNTING[i % BUNTING.length])}
            castShadow
          >
            <coneGeometry args={[0.24, 0.42, 3]} />
          </mesh>
        );
      })}

      {/* bank */}
      <group position={[cCx, platH, edgeZ + depth - 1.3]}>
        <mesh position={[0, 0.5, 0]} geometry={roundedBox(2.4, 0.14, 0.7, 0.06, 0.04)} material={paint('#4D9BFF')} castShadow />
        <mesh position={[0, 0.95, 0.32]} geometry={roundedBox(2.4, 0.6, 0.12, 0.05, 0.04)} material={paint('#4D9BFF')} castShadow />
        {[-1, 1].map((s) => (
          <mesh key={s} position={[s * 1.0, 0.24, 0]} material={paint('#34407A')} castShadow>
            <boxGeometry args={[0.12, 0.48, 0.6]} />
          </mesh>
        ))}
      </group>

      {/* lambalar */}
      {lamps.map((x) => (
        <group key={x} position={[x, platH, edgeZ + 1.2]}>
          <mesh position={[0, 1.4, 0]} material={paint('#34407A')} castShadow>
            <cylinderGeometry args={[0.07, 0.1, 2.8, 12]} />
          </mesh>
          <mesh position={[0, 2.95, 0]} material={paint('#FFF6C2', { emissive: '#FFE9A0', emissiveIntensity: 0.35 })}>
            <sphereGeometry args={[0.28, 20, 16]} />
          </mesh>
          <mesh position={[0, 3.22, 0]} material={paint('#34407A')}>
            <coneGeometry args={[0.32, 0.22, 20]} />
          </mesh>
        </group>
      ))}

      {/* çiçek saksıları */}
      {Array.from({ length: Math.floor(len / 5) }, (_, i) => {
        const x = x0 + 2 + i * 5;
        if (keepClear && x > keepClear[0] && x < keepClear[1]) return null;
        const col = BUNTING[(i * 2 + 1) % BUNTING.length];
        return (
          <group key={i} position={[x, platH, edgeZ + depth - 0.4]}>
            <mesh position={[0, 0.25, 0]} material={paint('#D9774A')} castShadow>
              <cylinderGeometry args={[0.32, 0.24, 0.5, 18]} />
            </mesh>
            {[0, 1, 2, 3, 4].map((k) => (
              <mesh key={k} position={[Math.cos(k * 1.26) * 0.18, 0.6 + (k % 2) * 0.08, Math.sin(k * 1.26) * 0.18]} material={paint(col, { roughness: 0.7 })} castShadow>
                <sphereGeometry args={[0.14, 12, 10]} />
              </mesh>
            ))}
            <mesh position={[0, 0.56, 0]} material={paint('#4DAF4A')}>
              <sphereGeometry args={[0.2, 12, 10]} />
            </mesh>
          </group>
        );
      })}

      {/* küçük istasyon binası (rayın karşı tarafında, kameraya bakar) */}
      <group position={building ?? [x0 + 3.4, platH, edgeZ + depth - 1.7]}>
        <mesh position={[0, 1.4, 0]} geometry={roundedBox(5.2, 2.8, 2.6, 0.25, 0.08)} material={paint('#FFF3D6', { roughness: 0.85 })} castShadow receiveShadow />
        <mesh position={[0, 3.2, 0]} geometry={roundedBox(5.8, 0.5, 3.2, 0.3, 0.12)} material={paint('#2F7BEA')} castShadow />
        <mesh position={[0, 3.75, 0]} scale={[2.6, 0.6, 1.4]} material={paint('#2F7BEA')} castShadow>
          <sphereGeometry args={[1, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2]} />
        </mesh>
        <mesh position={[-1.2, 1.0, 1.31]} geometry={roundedBox(0.95, 1.9, 0.08, 0.3, 0.03)} material={paint('#E8332F')} />
        {[0.5, 1.7].map((x) => (
          <group key={x} position={[x, 1.6, 1.31]}>
            <mesh rotation={[Math.PI / 2, 0, 0]} material={paint('#FFFFFF')}>
              <cylinderGeometry args={[0.42, 0.42, 0.06, 28]} />
            </mesh>
            <mesh position={[0, 0, 0.02]} rotation={[Math.PI / 2, 0, 0]} material={paint("#9ED8FF", { roughness: 0.2 })}>
              <cylinderGeometry args={[0.34, 0.34, 0.06, 28]} />
            </mesh>
          </group>
        ))}
      </group>
    </group>
  );
};

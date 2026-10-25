import * as THREE from 'three';
import type { Track } from './track';

/** Tren ölçüleri (birim). Tüm parçalar bu sabitlerden konumlanır. */
export const RAIL_TOP = 0.16;
export const GAUGE_HALF = 1.2; // tekerlek / ray yanal mesafesi

export const LOCO = {
  front: 3.15,
  rear: -3.35,
  driveWheelR: 0.62,
  frontWheelR: 0.42,
  /** Pandi'nin kabin içindeki kök noktası (ayak hizası, oturur poz). */
  seat: new THREE.Vector3(-2.05, 0.9, 0),
  /** Direksiyon merkezi. */
  steeringWheel: new THREE.Vector3(-1.57, 1.62, 0),
  chimneyTop: new THREE.Vector3(1.9, 3.64, 0),
} as const;

export const WAGON = {
  length: 3.9,
  wheelR: 0.46,
  floorY: 1.17,
} as const;

export const COUPLING_GAP = 0.6;
export const WAGON_COUNT = 6;

export const WAGON_COLORS = ['red', 'blue', 'yellow', 'green', 'purple', 'orange'] as const;
export type WagonColor = (typeof WAGON_COLORS)[number];

export interface CarSpec {
  kind: 'loco' | 'wagon';
  index: number; // vagonlar için 0..5
  /** Baş noktasından (lokomotifin önü) aracın merkezine olan mesafe. */
  centerOffset: number;
  front: number; // yerel ön uç X
  rear: number; // yerel arka uç X
}

export const CARS: CarSpec[] = (() => {
  const cars: CarSpec[] = [{ kind: 'loco', index: -1, centerOffset: LOCO.front, front: LOCO.front, rear: LOCO.rear }];
  let cursor = LOCO.front - LOCO.rear + COUPLING_GAP; // lokomotif arka ucu + boşluk
  for (let i = 0; i < WAGON_COUNT; i++) {
    cars.push({
      kind: 'wagon',
      index: i,
      centerOffset: cursor + WAGON.length / 2,
      front: WAGON.length / 2,
      rear: -WAGON.length / 2,
    });
    cursor += WAGON.length + COUPLING_GAP;
  }
  return cars;
})();

export const TRAIN_LENGTH = CARS[CARS.length - 1].centerOffset + WAGON.length / 2;

export interface CarTransform {
  position: THREE.Vector3;
  yaw: number;
}

/**
 * Her aracın dünya konumu: ön ve arka boji noktaları ray üzerine oturtulur,
 * araç bu iki nokta arasına hizalanır. Virajlarda da vagonlar raydan çıkmaz.
 */
export const carTransforms = (track: Track, headDistance: number): CarTransform[] =>
  CARS.map((c) => {
    const center = headDistance - c.centerOffset;
    const half = ((c.front - c.rear) / 2) * 0.7;
    const mid = (c.front + c.rear) / 2; // yerel merkez kayması (lokomotifte sıfır değil)
    const pf = track.point(center + mid + half);
    const pr = track.point(center + mid - half);
    const yaw = Math.atan2(-(pf.z - pr.z), pf.x - pr.x);
    const p = pf.clone().add(pr).multiplyScalar(0.5);
    // yerel merkez kaymasını geri al
    p.x -= Math.cos(yaw) * mid;
    p.z += Math.sin(yaw) * mid;
    return { position: p, yaw };
  });

/** Yerel bir noktayı (araç koordinatı) dünya koordinatına çevirir. */
export const carLocalToWorld = (t: CarTransform, local: THREE.Vector3) =>
  local.clone().applyAxisAngle(new THREE.Vector3(0, 1, 0), t.yaw).add(t.position);

/** Dünya noktasını araç yerel koordinatına çevirir. */
export const worldToCarLocal = (t: CarTransform, world: THREE.Vector3) =>
  world.clone().sub(t.position).applyAxisAngle(new THREE.Vector3(0, 1, 0), -t.yaw);

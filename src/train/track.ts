import * as THREE from 'three';

/**
 * Ray hattı. Tren yalnızca bu eğri üzerinde ilerler.
 * Mesafe (s) eğrinin başından itibaren birim cinsinden yay uzunluğudur.
 * İlk istasyon düz bölümde, x = -26..11 arasındadır (tren s = 308'de durur → baş x = 8).
 */
export const TRACK_POINTS: [number, number, number][] = [
  [-300, 0, 0],
  [-200, 0, 0],
  [-100, 0, 0],
  [0, 0, 0],
  [60, 0, 0],
  [110, 0, -6],
  [170, 0, -26],
  [240, 0, -30],
  [320, 0, -12],
  [400, 0, 8],
  [480, 0, 4],
  [560, 0, -18],
  [640, 0, -30],
  [720, 0, -20],
  [800, 0, 0],
  [880, 0, 10],
  [960, 0, 0],
  [1040, 0, -14],
  [1120, 0, -14],
  [1200, 0, 0],
  [1300, 0, 0],
];

export interface TrackFrame {
  position: THREE.Vector3;
  tangent: THREE.Vector3;
  /** Y ekseni etrafında dönüş: yerel +X ekseni ray yönüne bakar. */
  yaw: number;
}

export class Track {
  readonly curve: THREE.CatmullRomCurve3;
  readonly length: number;

  constructor(points: [number, number, number][] = TRACK_POINTS) {
    this.curve = new THREE.CatmullRomCurve3(
      points.map((p) => new THREE.Vector3(...p)),
      false,
      'centripetal',
    );
    this.curve.arcLengthDivisions = 6000;
    this.length = this.curve.getLength();
  }

  private u(s: number) {
    return THREE.MathUtils.clamp(s / this.length, 0, 1);
  }

  point(s: number, target = new THREE.Vector3()) {
    return this.curve.getPointAt(this.u(s), target);
  }

  frame(s: number): TrackFrame {
    const position = this.point(s);
    const tangent = this.curve.getTangentAt(this.u(s)).normalize();
    return { position, tangent, yaw: Math.atan2(-tangent.z, tangent.x) };
  }

  /** Raydan yana kaydırılmış nokta (sağ = +Z yönü, düz kısımda). */
  offsetPoint(s: number, side: number, up = 0) {
    const f = this.frame(s);
    const normal = new THREE.Vector3(-f.tangent.z, 0, f.tangent.x).normalize();
    return f.position.clone().addScaledVector(normal, side).add(new THREE.Vector3(0, up, 0));
  }
}

let shared: Track | null = null;
export const getTrack = () => {
  if (!shared) shared = new Track();
  return shared;
};

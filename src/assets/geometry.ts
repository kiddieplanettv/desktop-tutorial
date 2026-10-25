import * as THREE from 'three';

const cache = new Map<string, THREE.BufferGeometry>();
const memo = (key: string, make: () => THREE.BufferGeometry) => {
  let g = cache.get(key);
  if (!g) {
    g = make();
    cache.set(key, g);
  }
  return g;
};

const roundedRectShape = (w: number, h: number, r: number) => {
  const s = new THREE.Shape();
  const x = -w / 2;
  const y = -h / 2;
  s.moveTo(x + r, y);
  s.lineTo(x + w - r, y);
  s.quadraticCurveTo(x + w, y, x + w, y + r);
  s.lineTo(x + w, y + h - r);
  s.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  s.lineTo(x + r, y + h);
  s.quadraticCurveTo(x, y + h, x, y + h - r);
  s.lineTo(x, y + r);
  s.quadraticCurveTo(x, y, x + r, y);
  return s;
};

/**
 * Yuvarlatılmış kutu (oyuncak görünümü). Boyutlar dış ölçüdür, merkez orijindedir.
 * radius: köşe yuvarlaklığı (üstten bakış), bevel: kenar yumuşaklığı.
 */
export const roundedBox = (w: number, h: number, d: number, radius = 0.15, bevel = 0.06) =>
  memo(`rb:${w}:${h}:${d}:${radius}:${bevel}`, () => {
    const r = Math.min(radius, w / 2 - bevel - 0.001, d / 2 - bevel - 0.001);
    const shape = roundedRectShape(w - bevel * 2, d - bevel * 2, Math.max(0.001, r));
    const g = new THREE.ExtrudeGeometry(shape, {
      depth: Math.max(0.001, h - bevel * 2),
      bevelEnabled: true,
      bevelThickness: bevel,
      bevelSize: bevel,
      bevelSegments: 4,
      curveSegments: 10,
    });
    // Ekstrüzyon ekseni Z → Y'ye çevir, ortala.
    g.rotateX(-Math.PI / 2);
    g.translate(0, -(h - bevel * 2) / 2, 0);
    g.computeVertexNormals();
    return g;
  });

/**
 * Üstü açık, yuvarlatılmış duvarlı kasa (vagon gövdesi).
 * w×d dış ölçü, wall duvar kalınlığı, h yükseklik. Taban ayrı eklenir.
 */
export const roundedTub = (w: number, d: number, h: number, wall = 0.14, radius = 0.4) =>
  memo(`tub:${w}:${d}:${h}:${wall}:${radius}`, () => {
    const bevel = 0.05;
    const outer = roundedRectShape(w - bevel * 2, d - bevel * 2, radius);
    const inner = roundedRectShape(w - bevel * 2 - wall * 2, d - bevel * 2 - wall * 2, Math.max(0.05, radius - wall));
    outer.holes.push(inner);
    const g = new THREE.ExtrudeGeometry(outer, {
      depth: h - bevel * 2,
      bevelEnabled: true,
      bevelThickness: bevel,
      bevelSize: bevel * 0.6,
      bevelSegments: 4,
      curveSegments: 12,
    });
    g.rotateX(-Math.PI / 2);
    g.translate(0, bevel, 0);
    g.computeVertexNormals();
    return g;
  });

/** İki nokta arasında silindir için konum/dönüş/uzunluk. */
export const between = (a: THREE.Vector3, b: THREE.Vector3) => {
  const mid = a.clone().add(b).multiplyScalar(0.5);
  const dir = b.clone().sub(a);
  const len = dir.length();
  const quat = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.normalize());
  return { mid, quat, len };
};

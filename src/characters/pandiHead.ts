import * as THREE from 'three';
import { makeCanvas, memo } from '../assets/proceduralTextures';
import { rng } from '../animations/math';

/**
 * Pandi'nin kafası: alt kısmı hafif genişleyen elipsoit (referans görseldeki tombul yanaklar).
 * Yüz öğeleri (λ = yatay açı, φ = dikey açı) koordinatlarında tanımlanır;
 * bu sayede doku, 3B gözler ve burun her zaman aynı yüzey noktalarına oturur.
 */
export const HEAD_RADII = { a: 0.74, b: 0.6, c: 0.63 } as const;

/** φ'ye bağlı yanak genişlemesi: kafanın alt yarısı biraz daha geniş. */
const jowl = (sinPhi: number) => 1 + 0.09 * Math.max(0, -sinPhi) - 0.04 * Math.max(0, sinPhi);

/** Birim küre noktasını kafa yüzeyine taşır. */
const deformUnit = (x: number, y: number, z: number, out: THREE.Vector3) => {
  const k = jowl(y);
  return out.set(x * HEAD_RADII.a * k, y * HEAD_RADII.b, z * HEAD_RADII.c * k);
};

const unitDir = (lambda: number, phi: number) =>
  new THREE.Vector3(Math.cos(phi) * Math.sin(lambda), Math.sin(phi), Math.cos(phi) * Math.cos(lambda));

export const headPoint = (lambda: number, phi: number, scale = 1) => {
  const d = unitDir(lambda, phi);
  return deformUnit(d.x, d.y, d.z, new THREE.Vector3()).multiplyScalar(scale);
};

export const headNormal = (lambda: number, phi: number) => {
  const e = 0.002;
  const p = headPoint(lambda, phi);
  const pl = headPoint(lambda + e, phi).sub(p);
  const pp = headPoint(lambda, phi + e).sub(p);
  return new THREE.Vector3().crossVectors(pl, pp).normalize();
};

/** Küre geometrisini kafa biçimine dönüştürür (UV'ler korunur). */
export const makeHeadGeometry = (
  scale = 1,
  wSeg = 72,
  hSeg = 48,
  phiStart = 0,
  phiLength = Math.PI * 2,
  thetaStart = 0,
  thetaLength = Math.PI,
) => {
  const g = new THREE.SphereGeometry(1, wSeg, hSeg, phiStart, phiLength, thetaStart, thetaLength);
  const pos = g.attributes.position as THREE.BufferAttribute;
  const v = new THREE.Vector3();
  for (let i = 0; i < pos.count; i++) {
    deformUnit(pos.getX(i), pos.getY(i), pos.getZ(i), v).multiplyScalar(scale);
    pos.setXYZ(i, v.x, v.y, v.z);
  }
  g.computeVertexNormals();
  return g;
};

// --- Yüz yerleşimi (radyan) ---
export const FACE = {
  eye: { lambda: 0.29, phi: -0.05 },
  patch: { lambda: 0.355, phi: -0.12, rx: 0.285, ry: 0.335, tilt: 0.5 },
  nose: { lambda: 0, phi: -0.215 },
  mouth: { phi: -0.43 },
  cheek: { lambda: 0.6, phi: -0.42, r: 0.13 },
  brow: { lambda: 0.31, phi: 0.2 },
  ear: { lambda: 0.6, phi: 0.62 },
} as const;

/**
 * Kafanın ana renk dokusu: beyaz tüy, göz çevresindeki siyah lekeler, pembe yanaklar.
 * Eşdikdörtgen (equirect) eşleme: x = (0.25 + λ/2π)·W, y = (0.5 − φ/π)·H.
 */
export const headColorTexture = () =>
  memo('pandiHeadColor', () => {
    const W = 4096;
    const H = 2048;
    const { c, ctx } = makeCanvas(W, H);
    const X = (l: number) => (0.25 + l / (Math.PI * 2)) * W;
    const Y = (p: number) => (0.5 - p / Math.PI) * H;
    const R = W / (Math.PI * 2); // radyan başına piksel

    ctx.fillStyle = '#fbf8f4';
    ctx.fillRect(0, 0, W, H);

    // Göz lekeleri: üstü içe, altı dışa doğru eğik damla biçimi; tüylü kenar için bulanıklık.
    const drawPatch = (side: 1 | -1) => {
      const { lambda, phi, rx, ry, tilt } = FACE.patch;
      ctx.save();
      ctx.translate(X(side * lambda), Y(phi));
      ctx.rotate(-side * tilt);
      ctx.fillStyle = '#242022';
      ctx.beginPath();
      // damla: alt kısım daha geniş
      const w = rx * R;
      const h = ry * R;
      ctx.moveTo(0, -h);
      ctx.bezierCurveTo(w * 0.85, -h, w * 1.12, h * 0.15, w * 0.9, h * 0.6);
      ctx.bezierCurveTo(w * 0.62, h * 1.05, -w * 0.62, h * 1.05, -w * 0.9, h * 0.6);
      ctx.bezierCurveTo(-w * 1.12, h * 0.15, -w * 0.85, -h, 0, -h);
      ctx.fill();
      ctx.restore();
    };
    ctx.filter = 'blur(10px)';
    drawPatch(1);
    drawPatch(-1);
    ctx.filter = 'none';

    // Pembe yanaklar
    for (const side of [1, -1]) {
      const { lambda, phi, r } = FACE.cheek;
      const cx = X(side * lambda);
      const cy = Y(phi);
      const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, r * R);
      g.addColorStop(0, 'rgba(255,125,150,0.9)');
      g.addColorStop(0.55, 'rgba(255,150,170,0.55)');
      g.addColorStop(1, 'rgba(255,170,185,0)');
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.ellipse(cx, cy, r * R * 1.25, r * R, 0, 0, Math.PI * 2);
      ctx.fill();
    }

    // Tüy telleri: hafif gölgeli kısa çizgiler (lekelerin kenarını da tüylü yapar).
    const r = rng(42);
    ctx.lineCap = 'round';
    for (let i = 0; i < 26000; i++) {
      const x = r() * W;
      const y = r() * H;
      const a = Math.PI / 2 + (r() - 0.5) * 1.2;
      const len = 6 + r() * 14;
      const dark = r() < 0.5;
      ctx.strokeStyle = dark ? 'rgba(200,190,185,0.18)' : 'rgba(255,255,255,0.35)';
      ctx.lineWidth = 1.5 + r() * 1.5;
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(x + Math.cos(a) * len, y + Math.sin(a) * len);
      ctx.stroke();
    }
    // Leke kenarlarına dışa taşan koyu tüyler
    for (const side of [1, -1]) {
      const { lambda, phi, rx, ry } = FACE.patch;
      for (let i = 0; i < 700; i++) {
        const ang = r() * Math.PI * 2;
        const rr = 0.82 + r() * 0.16;
        const x = X(side * lambda) + Math.cos(ang) * rx * R * rr;
        const y = Y(phi) + Math.sin(ang) * ry * R * rr;
        const len = 4 + r() * 6;
        ctx.strokeStyle = 'rgba(36,32,34,0.35)';
        ctx.lineWidth = 1.2 + r();
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x + Math.cos(ang) * len, y + Math.sin(ang) * len);
        ctx.stroke();
      }
    }

    const t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace;
    t.anisotropy = 8;
    return t;
  });

/** Gövde dokusu: beyaz göğüs, omuzlarda siyah kuşak (dev panda deseni). */
export const bodyColorTexture = () =>
  memo('pandiBodyColor', () => {
    const W = 1024;
    const H = 512;
    const { c, ctx } = makeCanvas(W, H);
    ctx.fillStyle = '#fbf8f4';
    ctx.fillRect(0, 0, W, H);
    const Y = (p: number) => (0.5 - p / Math.PI) * H;
    ctx.filter = 'blur(4px)';
    ctx.fillStyle = '#242022';
    // omuz kuşağı
    ctx.fillRect(0, Y(1.0), W, Y(0.28) - Y(1.0));
    ctx.filter = 'none';
    const r = rng(3);
    for (let i = 0; i < 5000; i++) {
      const x = r() * W;
      const y = r() * H;
      ctx.strokeStyle = r() < 0.5 ? 'rgba(200,190,185,0.18)' : 'rgba(255,255,255,0.3)';
      ctx.lineWidth = 1 + r();
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(x + (r() - 0.5) * 4, y + 4 + r() * 6);
      ctx.stroke();
    }
    const t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace;
    return t;
  });

/** Göz dokusu: kutup noktası öne bakar; enlem halkaları göz bebeği / iris / koyu kenar olur. */
export const eyeTexture = () =>
  memo('pandiEye', () => {
    const W = 16;
    const H = 512;
    const { c, ctx } = makeCanvas(W, H);
    const g = ctx.createLinearGradient(0, 0, 0, H);
    // y = θ/π (θ: kutuptan açı)
    g.addColorStop(0, '#0c0605');
    g.addColorStop(0.13, '#100806');
    g.addColorStop(0.16, '#3a2216');
    g.addColorStop(0.23, '#5e3c27');
    g.addColorStop(0.27, '#3d2518');
    g.addColorStop(0.3, '#160d09');
    g.addColorStop(1, '#160d09');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);
    const t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace;
    return t;
  });

// --- Hareketli yüz katmanı (ağız, kaşlar) ---
export const FACE_PATCH = { l0: -0.62, l1: 0.62, p0: -0.68, p1: 0.42 } as const;

export interface FaceParams {
  smile: number;
  mouthOpen: number;
  surprise: number;
  browRaise: number;
}

/**
 * Ağzı ve kaşları şeffaf tuvale çizer. Değerler değiştikçe yeniden çizilir
 * (yalnızca o karenin parametrelerine bağlı → deterministik).
 */
export const drawFace = (ctx: CanvasRenderingContext2D, W: number, H: number, f: FaceParams) => {
  const { l0, l1, p0, p1 } = FACE_PATCH;
  const X = (l: number) => ((l - l0) / (l1 - l0)) * W;
  const Y = (p: number) => ((p1 - p) / (p1 - p0)) * H;
  const R = W / (l1 - l0);
  ctx.clearRect(0, 0, W, H);

  const s = f.surprise;
  const open = Math.max(f.mouthOpen, s * 0.9);
  const my = FACE.mouth.phi;

  // Burundan ağza ince çizgi
  ctx.strokeStyle = '#2a1714';
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.lineWidth = 0.012 * R;
  ctx.beginPath();
  ctx.moveTo(X(0), Y(FACE.nose.phi - 0.05));
  ctx.lineTo(X(0), Y(my + 0.035 - s * 0.01));
  ctx.stroke();

  // Ağız biçimi: gülümsemeden "O"ya yumuşak geçiş
  const halfW = (0.19 + 0.035 * f.smile) * (1 - s) + 0.07 * s;
  const cornerLift = (0.045 * f.smile) * (1 - s);
  const topY = my + 0.035 * (1 - s) + 0.06 * s; // üst dudak
  const depth = 0.02 + 0.2 * open; // alt dudak derinliği
  const cx = X(0);

  const left = [X(-halfW), Y(topY + cornerLift)] as const;
  const right = [X(halfW), Y(topY + cornerLift)] as const;

  if (open < 0.08 && s < 0.05) {
    // kapalı gülümseme çizgisi
    ctx.lineWidth = 0.02 * R;
    ctx.beginPath();
    ctx.moveTo(...left);
    ctx.quadraticCurveTo(cx, Y(topY - 0.07 - 0.04 * f.smile), ...right);
    ctx.stroke();
  } else {
    const topCtrl = Y(topY - 0.015 + 0.075 * s);
    const bottom = Y(topY - depth - 0.04 * s);
    const path = new Path2D();
    path.moveTo(...left);
    path.quadraticCurveTo(cx, topCtrl, ...right);
    path.bezierCurveTo(X(halfW * 0.95), bottom, X(-halfW * 0.95), bottom, ...left);
    path.closePath();
    ctx.fillStyle = '#5c1d1f';
    ctx.fill(path);
    // dil
    ctx.save();
    ctx.clip(path);
    ctx.fillStyle = '#ef8d9b';
    ctx.beginPath();
    ctx.ellipse(cx, bottom - 0.01 * R, halfW * 0.72 * R, depth * 0.55 * R, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
    ctx.lineWidth = 0.013 * R;
    ctx.strokeStyle = '#2a1714';
    ctx.stroke(path);
  }

  // Kaşlar: ince kavisler
  ctx.strokeStyle = '#242022';
  ctx.lineWidth = 0.022 * R;
  for (const side of [1, -1]) {
    const bx = X(side * FACE.brow.lambda);
    const by = Y(FACE.brow.phi + 0.06 * f.browRaise + 0.05 * s);
    const w = 0.085 * R;
    ctx.beginPath();
    ctx.moveTo(bx - w, by + 0.022 * R);
    ctx.quadraticCurveTo(bx, by - 0.03 * R, bx + w, by + 0.022 * R);
    ctx.stroke();
  }
};

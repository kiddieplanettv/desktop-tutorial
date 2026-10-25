import * as THREE from 'three';
import { rng } from '../animations/math';

/**
 * Prosedürel (kodla üretilen) dokular. Harici dosya gerekmez,
 * tohumlu rastgelelik sayesinde her render'da birebir aynı çıkar.
 */

const makeCanvas = (w: number, h: number) => {
  const c = document.createElement('canvas');
  c.width = w;
  c.height = h;
  const ctx = c.getContext('2d');
  if (!ctx) throw new Error('2D canvas oluşturulamadı');
  return { c, ctx };
};

const cache = new Map<string, THREE.Texture>();
const memo = <T extends THREE.Texture>(key: string, make: () => T): T => {
  const hit = cache.get(key);
  if (hit) return hit as T;
  const t = make();
  cache.set(key, t);
  return t;
};

/** Tüy telleri için yüksek frekanslı gürültü (fur kabukları alphaMap'i). */
export const strandNoiseTexture = () =>
  memo('strand', () => {
    const size = 256;
    const { c, ctx } = makeCanvas(size, size);
    const img = ctx.createImageData(size, size);
    const r = rng(7);
    for (let i = 0; i < size * size; i++) {
      const v = Math.floor(r() * 255);
      img.data[i * 4] = v;
      img.data[i * 4 + 1] = v;
      img.data[i * 4 + 2] = v;
      img.data[i * 4 + 3] = 255;
    }
    ctx.putImageData(img, 0, 0);
    const t = new THREE.CanvasTexture(c);
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.magFilter = THREE.NearestFilter;
    t.minFilter = THREE.NearestMipmapLinearFilter;
    return t;
  });

/** Yumuşak tüy kabartması için bump dokusu (kısa fırça darbeleri). */
export const furBumpTexture = () =>
  memo('furBump', () => {
    const size = 512;
    const { c, ctx } = makeCanvas(size, size);
    ctx.fillStyle = '#808080';
    ctx.fillRect(0, 0, size, size);
    const r = rng(11);
    ctx.lineCap = 'round';
    for (let i = 0; i < 9000; i++) {
      const x = r() * size;
      const y = r() * size;
      const a = Math.PI / 2 + (r() - 0.5) * 0.9;
      const len = 3 + r() * 7;
      const v = Math.floor(90 + r() * 90);
      ctx.strokeStyle = `rgb(${v},${v},${v})`;
      ctx.lineWidth = 0.8 + r() * 1.2;
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(x + Math.cos(a) * len, y + Math.sin(a) * len);
      ctx.stroke();
    }
    const t = new THREE.CanvasTexture(c);
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    return t;
  });

/** Hafif renk varyasyonlu kumaş/boya dokusu (tren, ev, istasyon için mat yüzey). */
export const paintGrainTexture = () =>
  memo('paintGrain', () => {
    const size = 256;
    const { c, ctx } = makeCanvas(size, size);
    ctx.fillStyle = '#808080';
    ctx.fillRect(0, 0, size, size);
    const r = rng(23);
    for (let i = 0; i < 6000; i++) {
      const v = Math.floor(110 + r() * 40);
      ctx.fillStyle = `rgba(${v},${v},${v},0.5)`;
      ctx.fillRect(r() * size, r() * size, 1 + r() * 2, 1 + r() * 2);
    }
    const t = new THREE.CanvasTexture(c);
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    return t;
  });

/** Çimen için hafif desenli renk dokusu. */
export const grassTexture = () =>
  memo('grass', () => {
    const size = 512;
    const { c, ctx } = makeCanvas(size, size);
    ctx.fillStyle = '#b4e69a';
    ctx.fillRect(0, 0, size, size);
    const r = rng(5);
    for (let i = 0; i < 14000; i++) {
      const g = 190 + Math.floor(r() * 50);
      ctx.fillStyle = `rgba(${150 + Math.floor(r() * 40)},${g + 10},${120 + Math.floor(r() * 40)},0.45)`;
      const x = r() * size;
      const y = r() * size;
      ctx.fillRect(x, y, 1.5, 3 + r() * 4);
    }
    const t = new THREE.CanvasTexture(c);
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.colorSpace = THREE.SRGBColorSpace;
    t.anisotropy = 4;
    return t;
  });

/** Yumuşak, kenarları saydam daire (buhar, ışık lekeleri). */
export const softDotTexture = () =>
  memo('softDot', () => {
    const size = 128;
    const { c, ctx } = makeCanvas(size, size);
    const g = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
    g.addColorStop(0, 'rgba(255,255,255,1)');
    g.addColorStop(0.6, 'rgba(255,255,255,0.6)');
    g.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, size, size);
    const t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace;
    return t;
  });

export { makeCanvas, memo };

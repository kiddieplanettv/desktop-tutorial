import * as THREE from 'three';
import { paintGrainTexture } from '../assets/proceduralTextures';

/**
 * Tren malzemeleri: parlak plastik değil, mat-saten boyalı ahşap oyuncak hissi.
 * Renkler çocukların doğru öğrenebileceği net, doygun tonlardadır.
 */
export const TRAIN_COLORS = {
  locoYellow: '#FFC83A',
  locoOrange: '#FF8A2B',
  chassis: '#34407A',
  wheelRim: '#2C376B',
  wheelHub: '#FFD25A',
  metal: '#C9CFD8',
  glass: '#BFE8FF',
  red: '#E8332F',
  blue: '#2F7BEA',
  yellow: '#FFD21F',
  green: '#35B84A',
  purple: '#8E4FD8',
  orange: '#FF8A1F',
} as const;

const cache = new Map<string, THREE.MeshStandardMaterial>();
export const paint = (color: string, opts: { roughness?: number; emissive?: string; emissiveIntensity?: number } = {}) => {
  const key = `${color}|${opts.roughness ?? 0.55}|${opts.emissive ?? ''}|${opts.emissiveIntensity ?? 0}`;
  let m = cache.get(key);
  if (!m) {
    const grain = paintGrainTexture();
    m = new THREE.MeshStandardMaterial({
      color,
      roughness: opts.roughness ?? 0.55,
      metalness: 0,
      bumpMap: grain,
      bumpScale: 0.25,
      emissive: opts.emissive ?? '#000000',
      emissiveIntensity: opts.emissiveIntensity ?? 0,
    });
    cache.set(key, m);
  }
  return m;
};

export const glassMaterial = () => {
  const key = 'glass';
  let m = cache.get(key);
  if (!m) {
    m = new THREE.MeshStandardMaterial({
      color: TRAIN_COLORS.glass,
      roughness: 0.08,
      transparent: true,
      opacity: 0.28,
      depthWrite: false,
    });
    cache.set(key, m);
  }
  return m;
};

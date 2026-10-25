import React, { useMemo } from 'react';
import { hash } from '../animations/math';
import type { Track } from '../train/track';
import { Bush, Cloud, Flowers, Hill, House, Tree, type FlowerSpec } from './Nature';

export type Exclude = (x: number, z: number) => boolean;

const PASTEL_FLOWERS = ['#FF6B6B', '#FFD93D', '#6BCBFF', '#C38BFF', '#FF9F43', '#FF8FB1', '#FFFFFF'];
const CROWNS = ['#5CC85A', '#6FD36A', '#4DBA5C', '#7ED957'];
const HILLS = ['#8FD873', '#9FE07F', '#7FCF6A', '#A8E48A'];
const HOUSE_STYLES = [
  { wall: '#FFF3D6', roof: '#F0614E' },
  { wall: '#E7F4FF', roof: '#4D9BFF' },
  { wall: '#FFEFF4', roof: '#C46BE0' },
  { wall: '#FFF8E1', roof: '#FF9F43' },
];

/**
 * Ray boyunca tohumlu (her render'da aynı) kır manzarası:
 * yuvarlak tepeler, ağaçlar, evler, çalılar, çiçekler ve bulutlar.
 */
export const Countryside: React.FC<{
  track: Track;
  from: number;
  to: number;
  time: number;
  seed?: number;
  exclude?: Exclude;
  flowerColors?: string[];
  flowerDensity?: number;
}> = ({ track, from, to, time, seed = 1, exclude = () => false, flowerColors = PASTEL_FLOWERS, flowerDensity = 1 }) => {
  const layout = useMemo(() => {
    const trees: { p: [number, number, number]; s: number; crown: string; seed: number }[] = [];
    const houses: { p: [number, number, number]; r: number; style: (typeof HOUSE_STYLES)[number] }[] = [];
    const hills: { p: [number, number, number]; r: number; h: number; c: string }[] = [];
    const bushes: { p: [number, number, number]; s: number }[] = [];
    const flowers: FlowerSpec[] = [];
    const clouds: { p: [number, number, number]; s: number; seed: number }[] = [];
    const s0 = Math.floor(from);
    const ok = (x: number, z: number) => !exclude(x, z);
    let k = seed * 1000;
    const r = () => hash(k++);

    for (let s = s0; s < to; s += 7) {
      for (const side of [-1, 1]) {
        // ağaçlar
        if (r() < 0.75) {
          const lat = side * (9 + r() * 24);
          const p = track.offsetPoint(s + r() * 6, lat);
          if (ok(p.x, p.z)) trees.push({ p: [p.x, 0, p.z], s: 0.8 + r() * 0.5, crown: CROWNS[Math.floor(r() * CROWNS.length)], seed: Math.floor(r() * 1000) });
        }
        // çalılar
        if (r() < 0.6) {
          const p = track.offsetPoint(s + r() * 6, side * (5.5 + r() * 6));
          if (ok(p.x, p.z)) bushes.push({ p: [p.x, 0, p.z], s: 0.7 + r() * 0.6 });
        }
        // çiçekler: küçük kümeler
        const clusters = Math.round(2 * flowerDensity);
        for (let c = 0; c < clusters; c++) {
          const base = track.offsetPoint(s + r() * 7, side * (4.2 + r() * 10));
          const color = flowerColors[Math.floor(r() * flowerColors.length)];
          for (let f = 0; f < 6; f++) {
            const x = base.x + (r() - 0.5) * 2.2;
            const z = base.z + (r() - 0.5) * 2.2;
            if (ok(x, z) && Math.abs(track.offsetPoint(s, 0).z - z) > 3.4) flowers.push({ x, z, color, scale: 0.85 + r() * 0.4 });
          }
        }
      }
      // evler (seyrek)
      if (r() < 0.22) {
        const side = r() < 0.65 ? -1 : 1;
        const p = track.offsetPoint(s, side * (16 + r() * 18));
        if (ok(p.x, p.z)) houses.push({ p: [p.x, 0, p.z], r: (r() - 0.5) * 0.8 + (side > 0 ? Math.PI : 0), style: HOUSE_STYLES[Math.floor(r() * HOUSE_STYLES.length)] });
      }
    }
    for (let s = s0 - 60; s < to + 60; s += 38) {
      for (const side of [-1, 1]) {
        const p = track.offsetPoint(s + r() * 20, side * (55 + r() * 70));
        hills.push({ p: [p.x, -1, p.z], r: 26 + r() * 30, h: 9 + r() * 12, c: HILLS[Math.floor(r() * HILLS.length)] });
      }
      const cp = track.offsetPoint(s + r() * 30, (r() < 0.75 ? -1 : 1) * (60 + r() * 80));
      clouds.push({ p: [cp.x, 24 + r() * 16, cp.z], s: 1.6 + r() * 1.4, seed: Math.floor(r() * 1000) });
    }
    return { trees, houses, hills, bushes, flowers, clouds };
  }, [track, from, to, seed, exclude, flowerColors, flowerDensity]);

  return (
    <group>
      {layout.hills.map((h, i) => (
        <Hill key={i} position={h.p} radius={h.r} height={h.h} color={h.c} />
      ))}
      {layout.trees.map((t, i) => (
        <Tree key={i} position={t.p} scale={t.s} crown={t.crown} seed={t.seed} time={time} />
      ))}
      {layout.houses.map((h, i) => (
        <House key={i} position={h.p} rotationY={h.r} wall={h.style.wall} roof={h.style.roof} />
      ))}
      {layout.bushes.map((b, i) => (
        <Bush key={i} position={b.p} scale={b.s} />
      ))}
      <Flowers items={layout.flowers} time={time} />
      {layout.clouds.map((c, i) => (
        <Cloud key={i} position={c.p} scale={c.s} seed={c.seed} time={time} />
      ))}
    </group>
  );
};

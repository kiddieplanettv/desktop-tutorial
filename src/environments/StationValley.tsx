import React, { useMemo } from 'react';
import { hash } from '../animations/math';
import type { Track } from '../train/track';
import { Countryside } from './Countryside';
import { Flowers, type FlowerSpec } from './Nature';
import { Station } from './Station';
import { Rails } from './Rails';
import { Ground } from './Ground';

/** İlk istasyonun konumu (dünya koordinatı, düz ray kısmı). */
export const FIRST_STATION = {
  x0: -28,
  x1: 12,
  canopyFrom: -17,
  canopyTo: -5,
  platformTop: 0.9,
  /** Pandi'nin beklediği nokta. */
  pandiSpot: [1.5, 0.9, 3.9] as [number, number, number],
} as const;

// Modül düzeyinde sabit (useMemo bağımlılıkları değişmesin diye).
const exclude = (x: number, z: number) =>
  // peron
  (x > FIRST_STATION.x0 - 2 && x < FIRST_STATION.x1 + 2 && z > 0.8 && z < 8) ||
  // kamera koridoru (ön planda görüşü kapatan ağaç/ev olmasın)
  (x > -24 && x < 34 && z > 8 && z < 34) ||
  // istasyon binası (rayın karşısı)
  (x > -14 && x < -4 && z > -10 && z < -3);

/**
 * İlk istasyonun çevresi: peron, raylar, kır manzarası ve ön planda çiçekler.
 * Sahne 1–3 bu ortamı kullanır.
 */
export const StationValley: React.FC<{ track: Track; time: number; focusX: number }> = ({ track, time, focusX }) => {
  const foreground = useMemo<FlowerSpec[]>(() => {
    const colors = ['#FF6B6B', '#FFD93D', '#6BCBFF', '#C38BFF', '#FF9F43', '#FF8FB1'];
    const out: FlowerSpec[] = [];
    for (let i = 0; i < 140; i++) {
      const x = -18 + hash(i * 3.1) * 40;
      const z = 8.6 + hash(i * 5.7) * 6;
      out.push({ x, z, color: colors[Math.floor(hash(i * 9.3) * colors.length)], scale: 0.9 + hash(i * 2.2) * 0.5 });
    }
    return out;
  }, []);
  return (
    <group>
      <Ground center={[focusX, 0]} />
      <Rails track={track} from={150} to={520} />
      <Station
        x0={FIRST_STATION.x0}
        x1={FIRST_STATION.x1}
        canopyFrom={FIRST_STATION.canopyFrom}
        canopyTo={FIRST_STATION.canopyTo}
        time={time}
        lamps={[FIRST_STATION.x0 + 2.5, FIRST_STATION.canopyTo + 1.2]}
        keepClear={[-4, 14]}
        building={[-9, 0, -6.5]}
      />
      <Countryside track={track} from={170} to={480} time={time} seed={3} exclude={exclude} />
      <Flowers items={foreground} time={time} />
    </group>
  );
};

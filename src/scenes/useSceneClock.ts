import { useCurrentFrame } from 'remotion';
import type { SceneProps } from './types';
import { NOMINAL_SCENE_SEC } from './types';

/**
 * Sahne saatleri:
 *  - t  : videonun genel saniyesi (tren, bulut, rüzgâr gibi süreklilik isteyen şeyler)
 *  - lt : sahnenin nominal yerel saniyesi 0..10 (karakter/kamera koreografisi)
 *  - u  : sahne ilerlemesi 0..1
 * Hepsi yalnızca kare numarasından hesaplanır.
 */
export const useSceneClock = ({ scene, tl }: SceneProps) => {
  const frame = useCurrentFrame();
  const u = frame / scene.durationInFrames;
  return {
    frame,
    globalFrame: scene.startFrame + frame,
    t: (scene.startFrame + frame) / tl.fps,
    lt: u * NOMINAL_SCENE_SEC,
    u,
  };
};

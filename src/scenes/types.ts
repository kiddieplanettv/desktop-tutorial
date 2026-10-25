import type { ResolvedScene, ResolvedTimeline } from '../timeline/timeline';

export interface SceneProps {
  scene: ResolvedScene;
  tl: ResolvedTimeline;
}

/** Storyboard'daki her sahnenin nominal süresi (sn). Sahne uzatılırsa hareketler orantılı esner. */
export const NOMINAL_SCENE_SEC = 10;

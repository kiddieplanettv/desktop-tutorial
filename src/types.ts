export type Move = "sway" | "bounce" | "armWave" | "jump" | "spin" | "slideLeftRight" | "clapUp";

export type Block = {
  from: number;
  durationInFrames: number;
  move: Move;
  energy: number;
};

export type Timeline = {
  fps: number;
  durationInFrames: number;
  intro: { from: number; durationInFrames: number };
  blocks: Block[];
  outro: { from: number; durationInFrames: number };
  beatFrames: number[];
  downbeatFrames: number[];
};

export type Props = {
  audio: string;
  timelinePath: string;
  timeline: Timeline | null;
};

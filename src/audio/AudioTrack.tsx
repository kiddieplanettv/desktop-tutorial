import React from 'react';
import { Html5Audio, Sequence, staticFile, useVideoConfig } from 'remotion';
import type { AudioTiming } from '../timeline/timeline';

/**
 * Sonradan eklenecek şarkı. src boşsa hiçbir şey çalmaz (video sessizdir).
 * startOffsetSec > 0 → şarkı videoda geç başlar; < 0 → şarkının başı kırpılır.
 */
export const AudioTrack: React.FC<{ audio: AudioTiming; enabled: boolean }> = ({ audio, enabled }) => {
  const { fps } = useVideoConfig();
  if (!enabled || !audio.src) return null;
  const offsetFrames = Math.round(audio.startOffsetSec * fps);
  const src = /^https?:/.test(audio.src) ? audio.src : staticFile(audio.src);
  return (
    <Sequence from={Math.max(0, offsetFrames)} name="Şarkı">
      <Html5Audio src={src} volume={audio.volume} trimBefore={offsetFrames < 0 ? -offsetFrames : undefined} />
    </Sequence>
  );
};

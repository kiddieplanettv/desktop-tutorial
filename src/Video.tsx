import React from 'react';
import { AbsoluteFill, Sequence } from 'remotion';
import { AudioTrack } from './audio/AudioTrack';
import { sceneComponent } from './scenes/registry';
import { DebugOverlay } from './timeline/DebugOverlay';
import { timingFromProps, type VideoProps } from './timeline/props';
import { getTimeline } from './timeline/timeline';

/**
 * Ana video: 21 sahne zaman çizelgesine arka arkaya dizilir.
 * Her sahne kendi <Sequence>'ında bağımsız çalışır; aralarında boş kare yoktur.
 */
export const PandiVideo: React.FC<VideoProps> = (props) => {
  const timing = timingFromProps(props);
  const tl = getTimeline(timing);
  return (
    <AbsoluteFill style={{ backgroundColor: '#BFE6FF' }}>
      {tl.scenes.map((s) => {
        const Scene = sceneComponent(s.id);
        return (
          <Sequence key={s.id} from={s.startFrame} durationInFrames={s.durationInFrames} name={`${s.number}. ${s.title}`} premountFor={20}>
            <Scene scene={s} tl={tl} />
          </Sequence>
        );
      })}
      <AudioTrack audio={timing.audio} enabled={props.audioEnabled} />
      {props.showGuides && <DebugOverlay tl={tl} />}
    </AbsoluteFill>
  );
};

/** Tek bir sahneyi tek başına oynatır (Studio'da sahne seçimi için). */
export const SingleScene: React.FC<VideoProps & { sceneId: string }> = ({ sceneId, ...props }) => {
  const tl = getTimeline(timingFromProps(props));
  const s = tl.byId[sceneId];
  const Scene = sceneComponent(sceneId);
  return (
    <AbsoluteFill style={{ backgroundColor: '#BFE6FF' }}>
      <Scene scene={s} tl={tl} />
      {props.showGuides && (
        <Sequence from={-s.startFrame} layout="none">
          <DebugOverlay tl={tl} />
        </Sequence>
      )}
    </AbsoluteFill>
  );
};

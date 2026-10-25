import React from 'react';
import { Composition, Folder } from 'remotion';
import { PandiVideo, SingleScene } from './Video';
import { defaultVideoProps, timingFromProps, videoSchema, type VideoProps } from './timeline/props';
import { DEFAULT_TIMING, getTimeline } from './timeline/timeline';
import { CharacterLab, characterLabSchema, ACTIONS, ACTION_SEC } from './labs/CharacterLab';
import { TrainLab, trainLabSchema } from './labs/TrainLab';
import { MusicSync } from './labs/MusicSync';
import { isImplemented } from './scenes/registry';

const { fps, width, height } = DEFAULT_TIMING;

const fullDuration = ({ props }: { props: VideoProps }) => ({
  durationInFrames: getTimeline(timingFromProps(props)).totalFrames,
});

export const RemotionRoot: React.FC = () => (
  <>
    {/* Ana video: 21 sahne, 210 sn, 6300 kare */}
    <Composition
      id="PandiTrain"
      component={PandiVideo}
      schema={videoSchema}
      defaultProps={defaultVideoProps}
      calculateMetadata={fullDuration}
      durationInFrames={6300}
      fps={fps}
      width={width}
      height={height}
    />
    {/* Prototip: ilk iki sahne (ilk 20 sn) — final video değildir */}
    <Composition
      id="Prototype20s"
      component={PandiVideo}
      schema={videoSchema}
      defaultProps={defaultVideoProps}
      calculateMetadata={({ props }) => {
        const tl = getTimeline(timingFromProps(props));
        return { durationInFrames: tl.byId.s02.endFrame };
      }}
      durationInFrames={600}
      fps={fps}
      width={width}
      height={height}
    />
    <Folder name="Sahneler">
      {DEFAULT_TIMING.scenes.map((s, i) => (
        <Composition
          key={s.id}
          id={`Sahne${String(i + 1).padStart(2, '0')}${isImplemented(s.id) ? '' : '-Bekliyor'}`}
          component={SingleScene}
          defaultProps={{ ...defaultVideoProps, sceneId: s.id }}
          calculateMetadata={({ props }) => ({
            durationInFrames: getTimeline(timingFromProps(props)).byId[s.id].durationInFrames,
          })}
          durationInFrames={300}
          fps={fps}
          width={width}
          height={height}
        />
      ))}
    </Folder>
    <Folder name="Kontrol">
      <Composition
        id="PandiEylemleri"
        component={CharacterLab}
        schema={characterLabSchema}
        defaultProps={{ action: 'tumu' as const, turntable: false, kamera: 'tam' as const, bpm: null }}
        calculateMetadata={({ props }) => ({
          durationInFrames: (props.action === 'tumu' ? ACTIONS.length : 1) * ACTION_SEC * fps,
        })}
        durationInFrames={ACTIONS.length * ACTION_SEC * fps}
        fps={fps}
        width={width}
        height={height}
      />
      <Composition
        id="TrenTesti"
        component={TrainLab}
        schema={trainLabSchema}
        defaultProps={{ speed: 5.5, camera: 'onCapraz' as const, steam: true }}
        durationInFrames={20 * fps}
        fps={fps}
        width={width}
        height={height}
      />
      <Composition
        id="MuzikSenkron"
        component={MusicSync}
        schema={videoSchema}
        defaultProps={defaultVideoProps}
        calculateMetadata={fullDuration}
        durationInFrames={6300}
        fps={fps}
        width={width}
        height={height}
      />
    </Folder>
  </>
);

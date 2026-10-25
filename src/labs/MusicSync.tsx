import React from 'react';
import { AbsoluteFill, Html5Audio, Sequence, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { getWaveformPortion, useAudioData } from '@remotion/media-utils';
import { timingFromProps, type VideoProps } from '../timeline/props';
import { formatTime, getTimeline } from '../timeline/timeline';
import { beatPhase } from '../animations/pandiActions';

const W = 1840;
const BAR_COUNT = 460;

/**
 * Müzik senkron aracı: şarkının dalga formu, sahne sınırları ve vuruş ızgarası
 * aynı zaman ekseninde gösterilir. Şarkı yoksa bunu açıkça belirtir.
 */
export const MusicSync: React.FC<VideoProps> = (props) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const timing = timingFromProps(props);
  const tl = getTimeline(timing);
  const src = timing.audio.src ? (/^https?:/.test(timing.audio.src) ? timing.audio.src : staticFile(timing.audio.src)) : null;
  const total = tl.totalSec;
  const X = (sec: number) => 40 + (sec / total) * W;
  const now = frame / fps;

  return (
    <AbsoluteFill style={{ background: '#0F1A33', color: 'white', fontFamily: 'Nunito, system-ui, sans-serif' }}>
      <div style={{ position: 'absolute', left: 40, top: 30, fontSize: 44, fontWeight: 900 }}>Müzik senkron · Pandi&apos;nin Renkli Treni</div>
      <div style={{ position: 'absolute', left: 40, top: 92, fontSize: 26, opacity: 0.8 }}>
        {src ? `Ses: ${timing.audio.src} · kayma ${timing.audio.startOffsetSec}s · BPM ${timing.audio.bpm ?? 'girilmedi'}` : 'Ses dosyası yok — public/audio/ içine koyup audioSrc alanına yazın.'}
      </div>
      {/* sahne blokları */}
      {tl.scenes.map((s, i) => (
        <div
          key={s.id}
          style={{
            position: 'absolute',
            left: X(s.startSec),
            width: X(s.endSec) - X(s.startSec) - 2,
            top: 170,
            height: 120,
            background: i % 2 ? '#2B3E6B' : '#33497D',
            borderRadius: 8,
            fontSize: 20,
            padding: 6,
            boxSizing: 'border-box',
            overflow: 'hidden',
          }}
        >
          <b>{s.number}</b>
          <div style={{ fontSize: 14, opacity: 0.85 }}>{s.title}</div>
          <div style={{ fontSize: 13, opacity: 0.6 }}>{formatTime(s.startSec)}</div>
        </div>
      ))}
      {src ? <Waveform src={src} total={total} offset={timing.audio.startOffsetSec} X={X} /> : null}
      {/* vuruş ızgarası (BPM girildiyse) */}
      {timing.audio.bpm
        ? Array.from({ length: Math.floor(beatPhase(total, timing.audio.bpm, timing.audio.beatOffsetSec)) + 1 }, (_, b) => {
            const sec = timing.audio.beatOffsetSec + (b * 60) / timing.audio.bpm!;
            if (sec < 0 || sec > total) return null;
            return <div key={b} style={{ position: 'absolute', left: X(sec), top: 320, width: 1, height: b % 4 === 0 ? 300 : 260, background: b % 4 === 0 ? '#FFD21F' : '#FFD21F55' }} />;
          })
        : null}
      {/* oynatma başı */}
      <div style={{ position: 'absolute', left: X(now), top: 160, width: 4, height: 800, background: '#FF5D5D' }} />
      <div style={{ position: 'absolute', left: 40, bottom: 40, fontSize: 30 }}>
        {formatTime(now)} / {formatTime(total)}
      </div>
      {src ? (
        <Sequence from={Math.max(0, Math.round(timing.audio.startOffsetSec * fps))}>
          <Html5Audio src={src} volume={timing.audio.volume} trimBefore={timing.audio.startOffsetSec < 0 ? Math.round(-timing.audio.startOffsetSec * fps) : undefined} />
        </Sequence>
      ) : null}
    </AbsoluteFill>
  );
};

const Waveform: React.FC<{ src: string; total: number; offset: number; X: (s: number) => number }> = ({ src, total, offset, X }) => {
  const data = useAudioData(src);
  if (!data) return <div style={{ position: 'absolute', left: 40, top: 360, fontSize: 28 }}>Ses yükleniyor…</div>;
  const dur = data.durationInSeconds;
  const bars = getWaveformPortion({ audioData: data, startTimeInSeconds: 0, durationInSeconds: dur, numberOfSamples: BAR_COUNT });
  return (
    <>
      {bars.map((b, i) => {
        const sec = offset + (i / BAR_COUNT) * dur;
        if (sec < 0 || sec > total) return null;
        const h = Math.max(2, b.amplitude * 520);
        return <div key={i} style={{ position: 'absolute', left: X(sec), top: 620 - h / 2, width: Math.max(1, (W / total) * (dur / BAR_COUNT) - 1), height: h, background: '#6BCBFF', borderRadius: 2 }} />;
      })}
    </>
  );
};

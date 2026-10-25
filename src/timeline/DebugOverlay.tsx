import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { formatTime, type ResolvedTimeline } from './timeline';
import { isImplemented } from '../scenes/registry';

/** Önizleme yardımcı katmanı: aktif sahne, başlangıç/bitiş, zaman kodu. Render'da varsayılan olarak kapalı. */
export const DebugOverlay: React.FC<{ tl: ResolvedTimeline }> = ({ tl }) => {
  const frame = useCurrentFrame();
  const scene = tl.scenes.find((s) => frame >= s.startFrame && frame < s.endFrame) ?? tl.scenes[tl.scenes.length - 1];
  const sec = frame / tl.fps;
  return (
    <AbsoluteFill style={{ pointerEvents: 'none', fontFamily: 'ui-monospace, Menlo, monospace' }}>
      <div
        style={{
          position: 'absolute',
          left: 24,
          top: 24,
          background: '#0B1530CC',
          color: 'white',
          padding: '14px 20px',
          borderRadius: 14,
          fontSize: 26,
          lineHeight: 1.35,
        }}
      >
        <div>
          Sahne {scene.number}/{tl.scenes.length} · {scene.title} {isImplemented(scene.id) ? '' : '(yapılmadı)'}
        </div>
        <div>
          {formatTime(scene.startSec)} → {formatTime(scene.endSec)} · şimdi {formatTime(sec)} · kare {frame}
        </div>
      </div>
      {/* logo / güvenli alan kılavuzu */}
      <div style={{ position: 'absolute', inset: '5%', border: '2px dashed #FFFFFF66', borderRadius: 12 }} />
    </AbsoluteFill>
  );
};

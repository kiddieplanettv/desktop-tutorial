import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { formatTime } from '../timeline/timeline';
import type { SceneProps } from './types';

/**
 * HENÜZ YAPILMAMIŞ SAHNE.
 * Bilerek animasyonsuz ve açıkça etiketlidir: prototip onayından sonra
 * bu sahneler gerçek 3B animasyonla değiştirilecek. Final videoya bu kart girmemelidir.
 */
export const PendingScene: React.FC<SceneProps> = ({ scene }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill
      style={{
        background: 'linear-gradient(180deg, #DDF1FF 0%, #F3FBFF 100%)',
        justifyContent: 'center',
        alignItems: 'center',
        fontFamily: 'Nunito, "Segoe UI", system-ui, sans-serif',
        color: '#24305E',
      }}
    >
      <div style={{ border: '6px dashed #7FA6D9', borderRadius: 40, padding: '60px 90px', maxWidth: 1300, background: '#FFFFFFCC' }}>
        <div style={{ fontSize: 40, fontWeight: 800, color: '#C2410C', letterSpacing: 2 }}>YAPIM AŞAMASINDA — FİNAL GÖRÜNTÜ DEĞİL</div>
        <div style={{ fontSize: 76, fontWeight: 900, marginTop: 20 }}>
          Sahne {scene.number}: {scene.title}
        </div>
        <div style={{ fontSize: 36, marginTop: 20, lineHeight: 1.4 }}>{scene.summary}</div>
        <div style={{ fontSize: 30, marginTop: 30, opacity: 0.7 }}>
          {formatTime(scene.startSec)} – {formatTime(scene.endSec)} · kare {scene.startFrame + frame}
        </div>
      </div>
    </AbsoluteFill>
  );
};

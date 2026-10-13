import { AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame } from "remotion";
import type { Props } from "./types";

// İskelet: intro / loop blokları / outro yerleşimini ve beat nabzını gösterir.
// Karakterler, dans hareketleri ve sahne bu yapının içine eklenecek.
const Label: React.FC<{ text: string; color: string }> = ({ text, color }) => (
  <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
    <div style={{ fontSize: 96, fontFamily: "sans-serif", color, fontWeight: 800 }}>{text}</div>
  </AbsoluteFill>
);

export const DancingAnimals: React.FC<Props> = ({ audio, timeline }) => {
  const frame = useCurrentFrame();
  if (!timeline) return null;

  const lastBeat = [...timeline.beatFrames].reverse().find((b) => b <= frame) ?? 0;
  const pulse = Math.max(0, 1 - (frame - lastBeat) / 8);

  return (
    <AbsoluteFill style={{ backgroundColor: "#3b1a7a" }}>
      <Audio src={staticFile(audio)} />
      <Sequence from={timeline.intro.from} durationInFrames={timeline.intro.durationInFrames}>
        <Label text="INTRO" color="#ffd166" />
      </Sequence>
      {timeline.blocks.map((b, i) => (
        <Sequence key={i} from={b.from} durationInFrames={b.durationInFrames}>
          <Label text={b.move} color="#ffffff" />
        </Sequence>
      ))}
      <Sequence from={timeline.outro.from} durationInFrames={timeline.outro.durationInFrames}>
        <Label text="OUTRO" color="#06d6a0" />
      </Sequence>
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", padding: 80 }}>
        <div
          style={{
            width: 60,
            height: 60,
            borderRadius: 30,
            background: "#ff6fb5",
            transform: `scale(${1 + pulse * 0.6})`,
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

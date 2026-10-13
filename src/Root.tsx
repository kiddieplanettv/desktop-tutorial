import { CalculateMetadataFunction, Composition, staticFile } from "remotion";
import { DancingAnimals } from "./DancingAnimals";
import type { Props, Timeline } from "./types";

// Video süresi her zaman timeline.json'dan (yani şarkının süresinden) gelir.
const calculateMetadata: CalculateMetadataFunction<Props> = async ({ props }) => {
  const res = await fetch(staticFile(props.timelinePath));
  const timeline = (await res.json()) as Timeline;
  return {
    durationInFrames: timeline.durationInFrames,
    fps: timeline.fps,
    props: { ...props, timeline },
  };
};

export const RemotionRoot: React.FC = () => (
  <Composition
    id="DancingAnimals"
    component={DancingAnimals}
    width={1920}
    height={1080}
    fps={30}
    durationInFrames={300}
    defaultProps={{
      audio: "audio/sample.mp3",
      timelinePath: "data/timeline.json",
      timeline: null,
    }}
    calculateMetadata={calculateMetadata}
  />
);

import { Composition } from "remotion";
import { Clip } from "./Clip";
import data from "./words.json";

// 9:16 vertical. Length and fps come from words.json, which cut.py writes.
export const Root = () => (
  <Composition
    id="Clip"
    component={Clip}
    width={1080}
    height={1920}
    fps={data.fps}
    durationInFrames={Math.ceil(data.dur * data.fps)}
  />
);

import { RoughCutBench } from "./RoughCutBench";
import { SceneShotsBench } from "./SceneShotsBench";

// Direct vertical coverage first, then the post-production rough-cut layer.
// The editor stays scene-level so it can work for any future scene that owns
// direct shot masters and Veo takes.
export function ScenesBench(): React.JSX.Element {
  return (
    <>
      <SceneShotsBench />
      <RoughCutBench />
    </>
  );
}

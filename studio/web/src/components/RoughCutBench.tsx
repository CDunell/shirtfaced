import { useEffect, useState } from "react";
import { Button } from "./ui";

import { fetchShotMasterScenes } from "../api/sceneShots";
import { RoughCutPanel } from "./RoughCutPanel";
import { SectionTitle } from "./chrome";

export function RoughCutBench(): React.JSX.Element {
  const [sceneKeys, setSceneKeys] = useState<string[]>([]);
  const [sceneKey, setSceneKey] = useState("W01-P28");

  useEffect(() => {
    void fetchShotMasterScenes().then((keys) => {
      setSceneKeys(keys);
      const first = keys[0];
      if (!keys.includes(sceneKey) && first) setSceneKey(first);
    });
  }, [sceneKey]);

  return (
    <div className="mt-[34px] border-t border-current pt-6">
      {sceneKeys.length > 1 ? (
        <div className="mb-2.5">
          <SectionTitle>Post scene</SectionTitle>
          <div className="flex flex-wrap gap-2">
            {sceneKeys.map((key) => (
              <Button
                key={key}
                size="compact"
                variant={key === sceneKey ? "primary" : "secondary"}
                onClick={() => setSceneKey(key)}
              >
                {key}
              </Button>
            ))}
          </div>
        </div>
      ) : null}
      <RoughCutPanel sceneKey={sceneKey} />
    </div>
  );
}

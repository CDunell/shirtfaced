import { useEffect, useState } from "react";
import { Button, KIND as BUTTON_KIND, SIZE } from "baseui/button";
import { useStyletron } from "baseui";

import { fetchShotMasterScenes } from "../api/sceneShots";
import { RoughCutPanel } from "./RoughCutPanel";
import { SectionTitle } from "./chrome";

export function RoughCutBench(): React.JSX.Element {
  const [css] = useStyletron();
  const [sceneKeys, setSceneKeys] = useState<string[]>([]);
  const [sceneKey, setSceneKey] = useState("W01-P28");

  useEffect(() => {
    void fetchShotMasterScenes().then((keys) => {
      setSceneKeys(keys);
      if (!keys.includes(sceneKey) && keys.length) setSceneKey(keys[0]);
    });
  }, [sceneKey]);

  return (
    <div className={css({ marginTop: "34px", paddingTop: "24px", borderTop: "1px solid currentColor" })}>
      {sceneKeys.length > 1 ? (
        <div className={css({ marginBottom: "10px" })}>
          <SectionTitle>Post scene</SectionTitle>
          <div className={css({ display: "flex", gap: "8px", flexWrap: "wrap" })}>
            {sceneKeys.map((key) => (
              <Button
                key={key}
                size={SIZE.compact}
                kind={key === sceneKey ? BUTTON_KIND.primary : BUTTON_KIND.secondary}
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

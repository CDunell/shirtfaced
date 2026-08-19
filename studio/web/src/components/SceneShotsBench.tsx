import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useStyletron } from "baseui";
import { Button, KIND as BUTTON_KIND, SIZE } from "baseui/button";
import { Input } from "baseui/input";
import { Notification, KIND as NOTIFICATION_KIND } from "baseui/notification";
import { Tag, KIND as TAG_KIND } from "baseui/tag";
import { ParagraphSmall, ParagraphXSmall } from "baseui/typography";

import { ApiError } from "../api/client";
import {
  animateSceneShotMaster,
  approveSceneShotMaster,
  fetchSceneShotMasters,
  fetchSceneShotTakes,
  fetchShotMasterScenes,
  registerSceneShotMaster,
  rejectSceneShotMaster,
  sceneShotPreview,
  sceneShotTakeSource,
  type SceneShotMaster,
  type SceneShotMasters,
  type SceneShotTake,
} from "../api/sceneShots";
import { PageTitle, SectionTitle } from "./chrome";

function cleanName(name: string): string {
  return (
    name
      .replace(/\.[^.]+$/, "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "") || "shot"
  );
}

export function SceneShotsBench(): React.JSX.Element {
  const [css, theme] = useStyletron();
  const [sceneKeys, setSceneKeys] = useState<string[]>([]);
  const [sceneKey, setSceneKey] = useState("W01-P28");
  const [scene, setScene] = useState<SceneShotMasters | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [takes, setTakes] = useState<Record<string, SceneShotTake[]>>({});
  const filesRef = useRef<HTMLInputElement>(null);

  const load = useCallback(async (key: string) => {
    const [keys, current] = await Promise.all([
      fetchShotMasterScenes(),
      fetchSceneShotMasters(key),
    ]);
    setSceneKeys(keys);
    setScene(current);
    const found: Record<string, SceneShotTake[]> = {};
    await Promise.all(
      current.shot_masters.map(async (shot) => {
        const rows = await fetchSceneShotTakes(shot.id);
        if (rows.length) found[shot.id] = rows;
      }),
    );
    setTakes(found);
  }, []);

  useEffect(() => {
    void load(sceneKey).catch((cause: unknown) => {
      setError(cause instanceof ApiError ? cause.message : "Scenes are unavailable.");
    });
  }, [load, sceneKey]);

  const act = useCallback(
    async (label: string, work: () => Promise<string | null>) => {
      setBusy(label);
      setError(null);
      setNote(null);
      try {
        const message = await work();
        await load(sceneKey);
        if (message) setNote(message);
      } catch (cause: unknown) {
        setError(cause instanceof ApiError ? cause.message : "That did not go through.");
      } finally {
        setBusy(null);
      }
    },
    [load, sceneKey],
  );

  const approved = scene?.approved_count ?? 0;
  const maximum = scene?.maximum_approved ?? 5;
  const candidates = useMemo(
    () => [...(scene?.shot_masters ?? [])].sort((a, b) => a.sort_order - b.sort_order),
    [scene],
  );

  const onUpload = useCallback(() => {
    const files = [...(filesRef.current?.files ?? [])];
    if (!files.length || !sceneKey.trim()) return;
    void act("upload", async () => {
      for (const file of files) {
        await registerSceneShotMaster(sceneKey.trim(), file, cleanName(file.name));
      }
      if (filesRef.current) filesRef.current.value = "";
      return `${String(files.length)} shot master${files.length === 1 ? "" : "s"} registered as candidates.`;
    });
  }, [act, sceneKey]);

  const card = css({
    border: `1px solid ${theme.colors.borderOpaque}`,
    borderRadius: "12px",
    overflow: "hidden",
    backgroundColor: theme.colors.backgroundSecondary,
    display: "flex",
    flexDirection: "column",
    minWidth: 0,
  });
  const controls = css({
    display: "flex",
    gap: "8px",
    flexWrap: "wrap",
    alignItems: "center",
  });
  const grid = css({
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
    gap: "12px",
    marginTop: "12px",
  });
  const mono = css({
    fontFamily: "monospace",
    fontSize: "11px",
    color: theme.colors.contentTertiary,
  });

  const renderShot = (shot: SceneShotMaster) => {
    const latest = takes[shot.id]?.[0] ?? null;
    const canApprove = shot.status !== "approved" && approved < maximum;
    return (
      <article key={shot.id} className={card}>
        <button
          type="button"
          onClick={() => window.open(sceneShotPreview(shot.asset.id), "_blank")}
          className={css({ border: 0, padding: 0, background: "transparent", cursor: "zoom-in" })}
        >
          <img
            src={sceneShotPreview(shot.asset.id)}
            alt={`${shot.scene_key} ${shot.name}`}
            className={css({ width: "100%", aspectRatio: "9 / 16", objectFit: "cover", display: "block" })}
          />
        </button>
        <div className={css({ padding: "10px", display: "flex", flexDirection: "column", gap: "8px" })}>
          <div className={css({ display: "flex", justifyContent: "space-between", gap: "8px", alignItems: "center" })}>
            <strong>{shot.name}</strong>
            <Tag
              closeable={false}
              kind={shot.status === "approved" ? TAG_KIND.positive : shot.status === "rejected" ? TAG_KIND.negative : TAG_KIND.neutral}
            >
              {shot.status}
            </Tag>
          </div>
          <span className={mono}>
            {shot.asset.width}×{shot.asset.height} · {shot.asset.sha256.slice(0, 12)}
          </span>

          {latest ? (
            <video
              key={latest.stamp}
              src={sceneShotTakeSource(shot.id, latest.stamp)}
              controls
              playsInline
              preload="metadata"
              className={css({ width: "100%", borderRadius: "8px", background: "#000" })}
            />
          ) : null}

          <div className={controls}>
            {shot.status === "approved" ? (
              <Button
                size={SIZE.compact}
                isLoading={busy === `animate-${shot.id}`}
                onClick={() => {
                  void act(`animate-${shot.id}`, async () => {
                    await animateSceneShotMaster(shot.id);
                    return `${shot.name}: Veo take generated.`;
                  });
                }}
              >
                Animate
              </Button>
            ) : (
              <Button
                size={SIZE.compact}
                disabled={!canApprove}
                isLoading={busy === `approve-${shot.id}`}
                onClick={() => {
                  void act(`approve-${shot.id}`, async () => {
                    await approveSceneShotMaster(shot.id);
                    return `${shot.name} approved for this scene.`;
                  });
                }}
              >
                Approve
              </Button>
            )}
            {shot.status !== "rejected" ? (
              <Button
                size={SIZE.compact}
                kind={BUTTON_KIND.secondary}
                isLoading={busy === `reject-${shot.id}`}
                onClick={() => {
                  void act(`reject-${shot.id}`, async () => {
                    await rejectSceneShotMaster(shot.id);
                    return `${shot.name} rejected.`;
                  });
                }}
              >
                Reject
              </Button>
            ) : null}
          </div>
        </div>
      </article>
    );
  };

  return (
    <>
      <PageTitle meta={`${String(approved)}/${String(maximum)} approved`}>Scenes</PageTitle>

      {error ? (
        <Notification kind={NOTIFICATION_KIND.negative} overrides={{ Body: { style: { width: "auto" } } }}>
          {error}
        </Notification>
      ) : null}
      {note ? (
        <Notification kind={NOTIFICATION_KIND.positive} overrides={{ Body: { style: { width: "auto" } } }}>
          {note}
        </Notification>
      ) : null}

      <SectionTitle>Scene</SectionTitle>
      <div className={controls}>
        <div className={css({ width: "220px" })}>
          <Input
            value={sceneKey}
            onChange={(event) => setSceneKey(event.currentTarget.value.toUpperCase())}
            placeholder="W01-P28"
            size={SIZE.compact}
          />
        </div>
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

      <ParagraphSmall>
        A scene now owns a small set of native vertical first frames. Register as many candidates as needed,
        approve at most five, then animate those exact frames. There is no 3×3 contact sheet and no panel extraction in this lane.
      </ParagraphSmall>

      <SectionTitle>Shot masters</SectionTitle>
      <div className={controls}>
        <input ref={filesRef} type="file" accept="image/png,image/jpeg,image/webp" multiple />
        <Button size={SIZE.compact} isLoading={busy === "upload"} onClick={onUpload}>
          Register files
        </Button>
        <ParagraphXSmall margin={0}>
          {String(candidates.length)} candidates · {String(approved)}/{String(maximum)} approved
        </ParagraphXSmall>
      </div>

      {candidates.length ? (
        <div className={grid}>{candidates.map(renderShot)}</div>
      ) : (
        <ParagraphSmall>No direct shot masters registered for {sceneKey} yet.</ParagraphSmall>
      )}
    </>
  );
}

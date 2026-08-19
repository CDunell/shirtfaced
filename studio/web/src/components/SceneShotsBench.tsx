import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useStyletron } from "baseui";
import { Button, KIND as BUTTON_KIND, SIZE } from "baseui/button";
import { Input } from "baseui/input";
import { Notification, KIND as NOTIFICATION_KIND } from "baseui/notification";
import { Tag, KIND as TAG_KIND } from "baseui/tag";
import { Textarea } from "baseui/textarea";
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
  replaceSceneShotMaster,
  saveSceneShotMotionPrompt,
  sceneShotPreview,
  sceneShotTakeSource,
  type SceneShotMaster,
  type SceneShotMasters,
  type SceneShotTake,
} from "../api/sceneShots";
import { PageTitle, SectionTitle } from "./chrome";

function cleanName(name: string): string {
  return name
    .replace(/\.[^.]+$/, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

function displayName(name: string): string {
  if (name.length <= 3) return name.toUpperCase();
  return name
    .split("-")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function statusKind(status: string) {
  if (status === "approved") return TAG_KIND.positive;
  if (status === "rejected") return TAG_KIND.negative;
  return TAG_KIND.neutral;
}

export function SceneShotsBench(): React.JSX.Element {
  const [css, theme] = useStyletron();
  const [sceneKeys, setSceneKeys] = useState<string[]>([]);
  const [sceneKey, setSceneKey] = useState("W01-P28");
  const [scene, setScene] = useState<SceneShotMasters | null>(null);
  const [selectedShotId, setSelectedShotId] = useState<string | null>(null);
  const [takes, setTakes] = useState<Record<string, SceneShotTake[]>>({});
  const [promptDraft, setPromptDraft] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [initialName, setInitialName] = useState("");
  const [newName, setNewName] = useState("");
  const [initialFileName, setInitialFileName] = useState("");
  const [newFileName, setNewFileName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const initialUploadRef = useRef<HTMLInputElement>(null);
  const replaceRef = useRef<HTMLInputElement>(null);
  const addRef = useRef<HTMLInputElement>(null);

  const load = useCallback(async (key: string, preserveShotId?: string | null) => {
    const [keys, current] = await Promise.all([
      fetchShotMasterScenes(),
      fetchSceneShotMasters(key),
    ]);
    setSceneKeys(keys);
    setScene(current);
    setSelectedShotId((currentId) => {
      const wanted = preserveShotId ?? currentId;
      return wanted && current.shot_masters.some((shot) => shot.id === wanted) ? wanted : null;
    });

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
    setSelectedShotId(null);
    setPromptDraft("");
    setShowAdd(false);
    void load(sceneKey, null).catch((cause: unknown) => {
      setError(cause instanceof ApiError ? cause.message : "Scenes are unavailable.");
    });
  }, [load, sceneKey]);

  const shots = useMemo(
    () => [...(scene?.shot_masters ?? [])].sort((a, b) => a.sort_order - b.sort_order),
    [scene],
  );
  const selected = useMemo(
    () => shots.find((shot) => shot.id === selectedShotId) ?? null,
    [selectedShotId, shots],
  );
  const latest = selected ? takes[selected.id]?.[0] ?? null : null;
  const approved = scene?.approved_count ?? 0;
  const maximum = scene?.maximum_approved ?? 5;

  useEffect(() => {
    setPromptDraft(selected?.motion_prompt ?? "");
    setShowAdd(false);
  }, [selected]);

  const act = useCallback(
    async (key: string, work: () => Promise<string | null>, preserve?: string | null) => {
      setBusy(key);
      setError(null);
      setNote(null);
      try {
        const message = await work();
        await load(sceneKey, preserve ?? selectedShotId);
        if (message) setNote(message);
      } catch (cause: unknown) {
        setError(cause instanceof ApiError ? cause.message : "That did not go through.");
      } finally {
        setBusy(null);
      }
    },
    [load, sceneKey, selectedShotId],
  );

  const controls = css({ display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center" });
  const panel = css({
    border: `1px solid ${theme.colors.borderOpaque}`,
    borderRadius: "14px",
    backgroundColor: theme.colors.backgroundSecondary,
    padding: "14px",
  });
  const mono = css({ fontFamily: "monospace", fontSize: "11px", color: theme.colors.contentTertiary });

  const initialSlug = cleanName(initialName);
  const newSlug = cleanName(newName);
  const initialDuplicate = shots.some((shot) => shot.name === initialSlug);
  const newDuplicate = shots.some((shot) => shot.name === newSlug);

  const onInitialUpload = useCallback(() => {
    const file = initialUploadRef.current?.files?.[0];
    const name = cleanName(initialName);
    if (!file || !name) return;
    void act("initial-upload", async () => {
      const created = await registerSceneShotMaster(sceneKey, file, name);
      setInitialName("");
      setInitialFileName("");
      if (initialUploadRef.current) initialUploadRef.current.value = "";
      setSelectedShotId(created.id);
      return `${name}: master added.`;
    }, null);
  }, [act, initialName, sceneKey]);

  const promptChanged = selected ? promptDraft !== (selected.motion_prompt ?? "") : false;
  const promptMissing = !promptDraft.trim();

  return (
    <>
      <PageTitle meta={`${String(approved)}/${String(maximum)} approved`}>
        {sceneKey}{scene?.title ? ` — ${scene.title}` : ""}
      </PageTitle>
      {scene?.description ? (
        <ParagraphSmall className={css({ maxWidth: "760px", marginTop: "-4px" })}>
          {scene.description}
        </ParagraphSmall>
      ) : null}

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

      {sceneKeys.length > 1 ? (
        <div className={css({ marginTop: "18px" })}>
          <SectionTitle>Scene</SectionTitle>
          <div className={controls}>
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

      {shots.length === 0 ? (
        <div className={css({ marginTop: "24px" })}>
          <SectionTitle>Add first shot master</SectionTitle>
          <div className={panel}>
            <ParagraphSmall>
              Choose the production Shot ID explicitly. The local filename is only a suggestion and is not the shot identity.
            </ParagraphSmall>
            <div className={css({ display: "flex", flexDirection: "column", gap: "10px", maxWidth: "520px" })}>
              <input
                ref={initialUploadRef}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                onChange={(event) => {
                  const file = event.currentTarget.files?.[0];
                  setInitialFileName(file?.name ?? "");
                  if (file && !initialName.trim()) setInitialName(cleanName(file.name));
                }}
              />
              <Input
                value={initialName}
                onChange={(event) => setInitialName(event.currentTarget.value)}
                placeholder="Shot ID, e.g. trio-wide"
                size={SIZE.compact}
              />
              <ParagraphXSmall margin={0}>
                Source: {initialFileName || "no file selected"} · Shot ID: <span className={mono}>{initialSlug || "—"}</span>
              </ParagraphXSmall>
              {initialDuplicate ? <ParagraphXSmall margin={0}>That Shot ID already exists.</ParagraphXSmall> : null}
              <div>
                <Button
                  size={SIZE.compact}
                  disabled={!initialFileName || !initialSlug || initialDuplicate}
                  isLoading={busy === "initial-upload"}
                  onClick={onInitialUpload}
                >
                  Add master
                </Button>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <>
          <div className={css({ marginTop: "24px" })}>
            <SectionTitle>Shot</SectionTitle>
            <div className={controls}>
              {shots.map((shot) => (
                <Button
                  key={shot.id}
                  size={SIZE.compact}
                  kind={shot.id === selectedShotId ? BUTTON_KIND.primary : BUTTON_KIND.secondary}
                  onClick={() => setSelectedShotId(shot.id)}
                >
                  {displayName(shot.name)} · {shot.status}
                </Button>
              ))}
            </div>
            {!selected ? (
              <ParagraphXSmall className={css({ color: theme.colors.contentTertiary })}>
                Select a shot to open its production workspace.
              </ParagraphXSmall>
            ) : null}
          </div>

          {selected ? (
            <section className={css({ marginTop: "20px" })}>
              <div className={css({ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "12px", flexWrap: "wrap", marginBottom: "10px" })}>
                <div>
                  <h2 className={css({ margin: 0, fontSize: "22px" })}>{displayName(selected.name)}</h2>
                  <span className={mono}>
                    {selected.name} · {selected.asset.width}×{selected.asset.height} · {selected.asset.sha256.slice(0, 12)}
                  </span>
                </div>
                <Tag closeable={false} kind={statusKind(selected.status)}>
                  {selected.status}
                </Tag>
              </div>

              <div className={css({ display: "grid", gridTemplateColumns: "minmax(240px, 360px) minmax(0, 1fr)", gap: "18px", alignItems: "start", "@media screen and (max-width: 760px)": { gridTemplateColumns: "1fr" } })}>
                <div>
                  <button
                    type="button"
                    onClick={() => window.open(sceneShotPreview(selected.asset.id), "_blank")}
                    className={css({ border: 0, padding: 0, background: "transparent", cursor: "zoom-in", width: "100%" })}
                  >
                    <img
                      src={sceneShotPreview(selected.asset.id)}
                      alt={`${selected.scene_key} ${selected.name}`}
                      className={css({ width: "100%", aspectRatio: "9 / 16", objectFit: "cover", display: "block", borderRadius: "12px" })}
                    />
                  </button>

                  <div className={css({ marginTop: "10px" })}>
                    <div className={controls}>
                      {selected.status !== "approved" ? (
                        <Button
                          size={SIZE.compact}
                          disabled={approved >= maximum}
                          isLoading={busy === `approve-${selected.id}`}
                          onClick={() => void act(`approve-${selected.id}`, async () => {
                            await approveSceneShotMaster(selected.id);
                            return `${selected.name} approved.`;
                          })}
                        >
                          Approve
                        </Button>
                      ) : null}
                      {selected.status !== "rejected" ? (
                        <Button
                          size={SIZE.compact}
                          kind={BUTTON_KIND.secondary}
                          isLoading={busy === `reject-${selected.id}`}
                          onClick={() => void act(`reject-${selected.id}`, async () => {
                            await rejectSceneShotMaster(selected.id);
                            return `${selected.name} rejected.`;
                          })}
                        >
                          Reject
                        </Button>
                      ) : null}
                    </div>
                  </div>
                </div>

                <div className={css({ display: "flex", flexDirection: "column", gap: "14px" })}>
                  <div className={panel}>
                    <div className={css({ display: "flex", justifyContent: "space-between", gap: "8px", alignItems: "center", marginBottom: "8px" })}>
                      <strong>Veo motion prompt</strong>
                      <Tag closeable={false} kind={promptMissing ? TAG_KIND.negative : TAG_KIND.neutral}>
                        {selected.motion_prompt_source === "override" ? "edited" : selected.motion_prompt_source === "configured" ? "default" : "missing"}
                      </Tag>
                    </div>
                    <Textarea
                      value={promptDraft}
                      onChange={(event) => setPromptDraft(event.currentTarget.value)}
                      placeholder="Describe the motion this first frame should perform."
                      overrides={{ Input: { style: { minHeight: "180px", fontFamily: "monospace", fontSize: "12px", lineHeight: "18px" } } }}
                    />
                    <div className={css({ display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center", marginTop: "8px" })}>
                      <Button
                        size={SIZE.compact}
                        kind={BUTTON_KIND.secondary}
                        disabled={!promptChanged || promptMissing}
                        isLoading={busy === `prompt-${selected.id}`}
                        onClick={() => void act(`prompt-${selected.id}`, async () => {
                          await saveSceneShotMotionPrompt(selected.id, promptDraft);
                          return `${selected.name}: prompt saved.`;
                        })}
                      >
                        Save prompt
                      </Button>
                      {selected.motion_prompt_source === "override" ? (
                        <Button
                          size={SIZE.compact}
                          kind={BUTTON_KIND.tertiary}
                          isLoading={busy === `reset-${selected.id}`}
                          onClick={() => void act(`reset-${selected.id}`, async () => {
                            await saveSceneShotMotionPrompt(selected.id, null);
                            return `${selected.name}: default prompt restored.`;
                          })}
                        >
                          Reset to default
                        </Button>
                      ) : null}
                    </div>
                  </div>

                  <div className={panel}>
                    <strong>Veo</strong>
                    <div className={css({ display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center", marginTop: "8px" })}>
                      <Button
                        size={SIZE.compact}
                        disabled={selected.status !== "approved" || promptMissing || promptChanged}
                        isLoading={busy === `animate-${selected.id}`}
                        onClick={() => void act(`animate-${selected.id}`, async () => {
                          await animateSceneShotMaster(selected.id);
                          return `${selected.name}: Veo take generated.`;
                        })}
                      >
                        {latest ? "Redo Veo" : "Animate"}
                      </Button>
                      {selected.status !== "approved" ? <ParagraphXSmall margin={0}>Approve this master before animation.</ParagraphXSmall> : null}
                    </div>

                    {latest ? (
                      <div className={css({ marginTop: "12px" })}>
                        <video
                          key={latest.stamp}
                          src={sceneShotTakeSource(selected.id, latest.stamp)}
                          controls
                          playsInline
                          preload="metadata"
                          className={css({ width: "100%", borderRadius: "10px", background: "#000" })}
                        />
                        <ParagraphXSmall marginBottom={0}>
                          Latest take · {latest.duration_seconds ? `${latest.duration_seconds.toFixed(1)}s` : "duration pending"}
                          {takes[selected.id]?.length ? ` · ${String(takes[selected.id].length)} total take${takes[selected.id].length === 1 ? "" : "s"}` : ""}
                        </ParagraphXSmall>
                      </div>
                    ) : (
                      <ParagraphXSmall>No Veo take yet.</ParagraphXSmall>
                    )}
                  </div>

                  <div className={panel}>
                    <strong>Master file</strong>
                    <ParagraphXSmall>
                      Shot ID <span className={mono}>{selected.name}</span> stays fixed on replacement. Replacing the pixels returns the shot to candidate for fresh approval.
                    </ParagraphXSmall>
                    <div className={controls}>
                      <input ref={replaceRef} type="file" accept="image/png,image/jpeg,image/webp" />
                      <Button
                        size={SIZE.compact}
                        kind={BUTTON_KIND.secondary}
                        isLoading={busy === `replace-${selected.id}`}
                        onClick={() => {
                          const file = replaceRef.current?.files?.[0];
                          if (!file) return;
                          void act(`replace-${selected.id}`, async () => {
                            await replaceSceneShotMaster(selected.id, file);
                            if (replaceRef.current) replaceRef.current.value = "";
                            return `${selected.name}: master replaced; approval required.`;
                          });
                        }}
                      >
                        Replace master
                      </Button>
                      <Button size={SIZE.compact} kind={BUTTON_KIND.tertiary} onClick={() => setShowAdd((value) => !value)}>
                        {showAdd ? "Cancel add" : "Add another master"}
                      </Button>
                    </div>

                    {showAdd ? (
                      <div className={css({ marginTop: "12px", display: "flex", flexDirection: "column", gap: "8px", maxWidth: "520px" })}>
                        <ParagraphXSmall margin={0}>
                          Set the production Shot ID. The selected file name is only used to suggest a starting value.
                        </ParagraphXSmall>
                        <input
                          ref={addRef}
                          type="file"
                          accept="image/png,image/jpeg,image/webp"
                          onChange={(event) => {
                            const file = event.currentTarget.files?.[0];
                            setNewFileName(file?.name ?? "");
                            if (file && !newName.trim()) setNewName(cleanName(file.name));
                          }}
                        />
                        <Input
                          value={newName}
                          onChange={(event) => setNewName(event.currentTarget.value)}
                          placeholder="Shot ID, e.g. brock-pint"
                          size={SIZE.compact}
                        />
                        <ParagraphXSmall margin={0}>
                          Source: {newFileName || "no file selected"} · Shot ID: <span className={mono}>{newSlug || "—"}</span>
                        </ParagraphXSmall>
                        {newDuplicate ? <ParagraphXSmall margin={0}>That Shot ID already exists. Use Replace master on that shot instead.</ParagraphXSmall> : null}
                        <div>
                          <Button
                            size={SIZE.compact}
                            kind={BUTTON_KIND.secondary}
                            disabled={!newFileName || !newSlug || newDuplicate}
                            isLoading={busy === "add-master"}
                            onClick={() => {
                              const file = addRef.current?.files?.[0];
                              const name = cleanName(newName);
                              if (!file || !name) return;
                              void (async () => {
                                setBusy("add-master");
                                setError(null);
                                setNote(null);
                                try {
                                  const created = await registerSceneShotMaster(sceneKey, file, name);
                                  setNewName("");
                                  setNewFileName("");
                                  setShowAdd(false);
                                  if (addRef.current) addRef.current.value = "";
                                  await load(sceneKey, created.id);
                                  setNote(`${name}: master added.`);
                                } catch (cause: unknown) {
                                  setError(cause instanceof ApiError ? cause.message : "That did not go through.");
                                } finally {
                                  setBusy(null);
                                }
                              })();
                            }}
                          >
                            Add master
                          </Button>
                        </div>
                      </div>
                    ) : null}
                  </div>
                </div>
              </div>
            </section>
          ) : null}
        </>
      )}
    </>
  );
}

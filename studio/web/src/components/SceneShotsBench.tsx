import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button, Input, Notification, Tag, type TagKind, Textarea, ParagraphSmall, ParagraphXSmall } from "./ui";

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

function statusKind(status: string): TagKind {
  if (status === "approved") return "positive";
  if (status === "rejected") return "negative";
  return "neutral";
}

const controls = "flex flex-wrap items-center gap-2";
const panel = "rounded-[14px] border border-paper-2 bg-paper-2 p-3.5";
const mono = "font-mono text-[11px] text-ink/50";

export function SceneShotsBench(): React.JSX.Element {
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
        <ParagraphSmall className="-mt-1 max-w-[760px]">{scene.description}</ParagraphSmall>
      ) : null}

      {error ? <Notification kind="negative">{error}</Notification> : null}
      {note ? <Notification kind="positive">{note}</Notification> : null}

      {sceneKeys.length > 1 ? (
        <div className="mt-[18px]">
          <SectionTitle>Scene</SectionTitle>
          <div className={controls}>
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

      {shots.length === 0 ? (
        <div className="mt-6">
          <SectionTitle>Add first shot master</SectionTitle>
          <div className={panel}>
            <ParagraphSmall>
              Choose the production Shot ID explicitly. The local filename is only a suggestion and is not the shot identity.
            </ParagraphSmall>
            <div className="flex max-w-[520px] flex-col gap-2.5">
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
              />
              <ParagraphXSmall className="m-0">
                Source: {initialFileName || "no file selected"} · Shot ID: <span className={mono}>{initialSlug || "—"}</span>
              </ParagraphXSmall>
              {initialDuplicate ? <ParagraphXSmall className="m-0">That Shot ID already exists.</ParagraphXSmall> : null}
              <div>
                <Button
                  size="compact"
                  disabled={!initialFileName || !initialSlug || initialDuplicate || busy === "initial-upload"}
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
          <div className="mt-6">
            <SectionTitle>Shot</SectionTitle>
            <div className={controls}>
              {shots.map((shot) => (
                <Button
                  key={shot.id}
                  size="compact"
                  variant={shot.id === selectedShotId ? "primary" : "secondary"}
                  onClick={() => setSelectedShotId(shot.id)}
                >
                  {displayName(shot.name)} · {shot.status}
                </Button>
              ))}
            </div>
            {!selected ? (
              <ParagraphXSmall className="text-ink/50">
                Select a shot to open its production workspace.
              </ParagraphXSmall>
            ) : null}
          </div>

          {selected ? (
            <section className="mt-5">
              <div className="mb-2.5 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="m-0 text-[22px]">{displayName(selected.name)}</h2>
                  <span className={mono}>
                    {selected.name} · {selected.asset.width}×{selected.asset.height} · {selected.asset.sha256.slice(0, 12)}
                  </span>
                </div>
                <Tag kind={statusKind(selected.status)}>{selected.status}</Tag>
              </div>

              <div className="grid grid-cols-[minmax(240px,360px)_minmax(0,1fr)] items-start gap-[18px] max-[760px]:grid-cols-1">
                <div>
                  <button
                    type="button"
                    onClick={() => window.open(sceneShotPreview(selected.asset.id), "_blank")}
                    className="w-full cursor-zoom-in border-0 bg-transparent p-0"
                  >
                    <img
                      src={sceneShotPreview(selected.asset.id)}
                      alt={`${selected.scene_key} ${selected.name}`}
                      className="block aspect-[9/16] w-full rounded-xl object-cover"
                    />
                  </button>

                  <div className="mt-2.5">
                    <div className={controls}>
                      {selected.status !== "approved" ? (
                        <Button
                          size="compact"
                          disabled={approved >= maximum || busy === `approve-${selected.id}`}
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
                          size="compact"
                          variant="secondary"
                          disabled={busy === `reject-${selected.id}`}
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

                <div className="flex flex-col gap-3.5">
                  <div className={panel}>
                    <div className="mb-2 flex items-center justify-between gap-2">
                      <strong>Veo motion prompt</strong>
                      <Tag kind={promptMissing ? "negative" : "neutral"}>
                        {selected.motion_prompt_source === "override" ? "edited" : selected.motion_prompt_source === "configured" ? "default" : "missing"}
                      </Tag>
                    </div>
                    <Textarea
                      value={promptDraft}
                      onChange={(event) => setPromptDraft(event.currentTarget.value)}
                      placeholder="Describe the motion this first frame should perform."
                      className="min-h-[180px] font-mono text-[12px] leading-[18px]"
                    />
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <Button
                        size="compact"
                        variant="secondary"
                        disabled={!promptChanged || promptMissing || busy === `prompt-${selected.id}`}
                        onClick={() => void act(`prompt-${selected.id}`, async () => {
                          await saveSceneShotMotionPrompt(selected.id, promptDraft);
                          return `${selected.name}: prompt saved.`;
                        })}
                      >
                        Save prompt
                      </Button>
                      {selected.motion_prompt_source === "override" ? (
                        <Button
                          size="compact"
                          variant="ghost"
                          disabled={busy === `reset-${selected.id}`}
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
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <Button
                        size="compact"
                        disabled={selected.status !== "approved" || promptMissing || promptChanged || busy === `animate-${selected.id}`}
                        onClick={() => void act(`animate-${selected.id}`, async () => {
                          await animateSceneShotMaster(selected.id);
                          return `${selected.name}: Veo take generated.`;
                        })}
                      >
                        {latest ? "Redo Veo" : "Animate"}
                      </Button>
                      {selected.status !== "approved" ? <ParagraphXSmall className="m-0">Approve this master before animation.</ParagraphXSmall> : null}
                    </div>

                    {latest ? (
                      <div className="mt-3">
                        <video
                          key={latest.stamp}
                          src={sceneShotTakeSource(selected.id, latest.stamp)}
                          controls
                          playsInline
                          preload="metadata"
                          className="w-full rounded-[10px] bg-black"
                        />
                        <ParagraphXSmall className="mb-0">
                          Latest take · {latest.duration_seconds ? `${latest.duration_seconds.toFixed(1)}s` : "duration pending"}
                          {(() => {
                            const selectedTakes = takes[selected.id];
                            if (!selectedTakes?.length) return "";
                            return ` · ${String(selectedTakes.length)} total take${selectedTakes.length === 1 ? "" : "s"}`;
                          })()}
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
                        size="compact"
                        variant="secondary"
                        disabled={busy === `replace-${selected.id}`}
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
                      <Button size="compact" variant="ghost" onClick={() => setShowAdd((value) => !value)}>
                        {showAdd ? "Cancel add" : "Add another master"}
                      </Button>
                    </div>

                    {showAdd ? (
                      <div className="mt-3 flex max-w-[520px] flex-col gap-2">
                        <ParagraphXSmall className="m-0">
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
                        />
                        <ParagraphXSmall className="m-0">
                          Source: {newFileName || "no file selected"} · Shot ID: <span className={mono}>{newSlug || "—"}</span>
                        </ParagraphXSmall>
                        {newDuplicate ? <ParagraphXSmall className="m-0">That Shot ID already exists. Use Replace master on that shot instead.</ParagraphXSmall> : null}
                        <div>
                          <Button
                            size="compact"
                            variant="secondary"
                            disabled={!newFileName || !newSlug || newDuplicate || busy === "add-master"}
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

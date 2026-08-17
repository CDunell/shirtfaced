/**
 * Running a scene, rather than filing the results of having run it elsewhere.
 *
 * The pipeline in NANO_BANANA_CONTACT_SHEET_PIPELINE.md is three provider calls
 * with a review after each. Studio used to do none of the calls and all of the
 * filing: generate a sheet somewhere else, download it, upload it back, and type
 * in the reference IDs from memory. So the screen asked an operator to know
 * UUIDs, which nobody does.
 *
 * Now: pick the people by name, press Generate, and the master, the references
 * and the scene's own coverage prompt are resolved from the library. Press a
 * panel to extract it. The only decisions left are the ones that are actually
 * decisions — which master, and whether what came back is any good.
 *
 * Approve and reject are both real. Rejecting keeps the take: a rerun is a new
 * call, never an overwrite, and a bad take is evidence about the prompt.
 *
 * The last stage is motion, and it is the one that behaves least like the
 * others. A shot does not get animated once — it accumulates takes, most of
 * them wrong, and the work is watching them and saying which seconds are the
 * good ones. So takes are listed in full, rejected ones included, and the
 * keeper range is typed against a clip that is playing on the same screen.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useStyletron } from "baseui";
import { Button, KIND as BUTTON_KIND, SIZE } from "baseui/button";
import { Checkbox } from "baseui/checkbox";
import { Input } from "baseui/input";
import { Textarea } from "baseui/textarea";
import { Notification, KIND as NOTIFICATION_KIND } from "baseui/notification";
import { Tag, KIND as TAG_KIND } from "baseui/tag";
import { LabelSmall, ParagraphXSmall } from "baseui/typography";

import { PageTitle, SectionTitle } from "./chrome";
import { ApiError } from "../api/client";
import {
  approveContactSheet,
  approveCoverage,
  approveMaster,
  extractPanel,
  fetchPipelineInputs,
  fetchScenes,
  fetchTakes,
  generateSheet,
  generateTake,
  keepTake,
  previewSource,
  registerMaster,
  rejectMotionTake,
  rejectTake,
  takeVideoSource,
  type ContactSheet,
  type CoverageFrame,
  type MotionTake,
  type PipelineInputs,
  type Scene,
} from "../api/production";

function shortSha(sha: string): string {
  return sha.slice(0, 12);
}

function seconds(ms: number | null): string {
  return ms === null ? "unknown length" : `${(ms / 1000).toFixed(1)}s`;
}

/** Milliseconds from a typed field, or null for anything that is not a number. */
function asMilliseconds(value: string): number | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  const parsed = Number(trimmed);
  return Number.isFinite(parsed) && parsed >= 0 ? Math.round(parsed) : null;
}

export function ScenesBench(): React.JSX.Element {
  const [css, theme] = useStyletron();
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [inputs, setInputs] = useState<PipelineInputs | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);

  const [newScene, setNewScene] = useState("");
  const [approveMasterOnUpload, setApproveMasterOnUpload] = useState(false);
  const masterInput = useRef<HTMLInputElement>(null);

  const [picked, setPicked] = useState<Set<string>>(new Set());
  const [promptName, setPromptName] = useState<string | null>(null);
  const [shotNames, setShotNames] = useState<Record<number, string>>({});

  const [takes, setTakes] = useState<MotionTake[]>([]);
  const [motionEdit, setMotionEdit] = useState<string | null>(null);
  const [ranges, setRanges] = useState<Record<string, { from: string; to: string }>>({});

  const reload = useCallback(async (sceneKey: string | null) => {
    const data = await fetchScenes();
    setScenes(data);
    const key = sceneKey ?? data[0]?.scene_key ?? null;
    setInputs(key ? await fetchPipelineInputs(key) : null);
    setTakes(key ? await fetchTakes(key) : []);
    return key;
  }, []);

  useEffect(() => {
    fetchScenes()
      .then(async (data) => {
        setScenes(data);
        const key = data[0]?.scene_key ?? null;
        setSelected(key);
        if (key) {
          setInputs(await fetchPipelineInputs(key));
          setTakes(await fetchTakes(key));
        }
        setLoading(false);
      })
      .catch((cause: unknown) => {
        setError(cause instanceof ApiError ? cause.message : "Scenes are unavailable.");
        setLoading(false);
      });
  }, []);

  const act = useCallback(
    async (what: string, work: () => Promise<string | null>) => {
      setBusy(what);
      setError(null);
      setNote(null);
      try {
        const message = await work();
        await reload(selected);
        if (message) setNote(message);
      } catch (cause) {
        setError(cause instanceof ApiError ? cause.message : "That did not go through.");
      } finally {
        setBusy(null);
      }
    },
    [reload, selected],
  );

  const motionPrompt = motionEdit ?? inputs?.motion_prompt ?? "";

  const scene = useMemo(
    () => scenes.find((one) => one.scene_key === selected) ?? null,
    [scenes, selected],
  );
  const master = scene?.masters.find((one) => one.id === scene.approved_master_id) ?? null;
  const sheets: ContactSheet[] = master?.contact_sheets ?? [];
  const approvedSheet = sheets.find((one) => one.status === "approved") ?? null;
  const frames: CoverageFrame[] = master?.coverage ?? [];
  const frameByPanel = new Map(frames.filter((one) => one.panel !== null).map((f) => [f.panel, f]));

  const chooseScene = useCallback((key: string) => {
    setSelected(key);
    setNote(null);
    setPicked(new Set());
    setMotionEdit(null);
    void fetchPipelineInputs(key).then(setInputs);
    void fetchTakes(key).then(setTakes);
  }, []);

  const onRegisterMaster = useCallback(() => {
    const file = masterInput.current?.files?.[0];
    const key = (scene?.scene_key ?? newScene).trim();
    if (!file || !key) return;

    void act("master", async () => {
      await registerMaster(key, file, { approve: approveMasterOnUpload });
      if (masterInput.current) masterInput.current.value = "";
      setSelected(key);
      setNewScene("");
      return approveMasterOnUpload
        ? `${key} has a master.`
        : `Registered as a candidate. Approve it to run the pipeline against it.`;
    });
  }, [act, approveMasterOnUpload, newScene, scene]);

  const onGenerate = useCallback(() => {
    if (!scene) return;
    void act("sheet", async () => {
      const stamp = new Date().toISOString().slice(0, 16).replace(/[-:T]/g, "");
      await generateSheet(scene.scene_key, {
        label: `${scene.scene_key}-coverage-${stamp}`,
        selections: [...picked],
        ...(promptName ? { prompt_name: promptName } : {}),
      });
      return "Nano returned a sheet. Look at it, then approve or reject.";
    });
  }, [act, picked, promptName, scene]);

  const onExtract = useCallback(
    (panel: number) => {
      if (!scene) return;
      const name = (shotNames[panel] ?? `panel-${String(panel)}`).trim();
      void act(`panel-${String(panel)}`, async () => {
        await extractPanel(scene.scene_key, { panel, name, selections: [...picked] });
        return `Panel ${String(panel)} came back as ${name}. Approve it to let Veo animate it.`;
      });
    },
    [act, picked, scene, shotNames],
  );

  const onAnimate = useCallback(
    (name: string) => {
      if (!scene) return;
      void act(`animate-${name}`, async () => {
        await generateTake(scene.scene_key, {
          name,
          ...(motionPrompt.trim() ? { prompt: motionPrompt.trim() } : {}),
        });
        return `Veo returned a take of ${name}. Watch it, then keep or reject it.`;
      });
    },
    [act, motionPrompt, scene],
  );

  const onKeep = useCallback(
    (take: MotionTake) => {
      const range = ranges[take.id] ?? { from: "", to: "" };
      void act(`keep-${take.id}`, async () => {
        await keepTake(take.id, {
          keeper_from_ms: asMilliseconds(range.from),
          keeper_to_ms: asMilliseconds(range.to),
        });
        return `Attempt ${String(take.attempt)} is the keeper for ${take.shot}.`;
      });
    },
    [act, ranges],
  );

  const takesByShot = useMemo(() => {
    const grouped = new Map<string, MotionTake[]>();
    for (const take of takes) grouped.set(take.shot, [...(grouped.get(take.shot) ?? []), take]);
    return grouped;
  }, [takes]);

  const card = css({
    border: `1px solid ${theme.colors.borderOpaque}`,
    borderRadius: "10px",
    padding: "10px",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    background: theme.colors.backgroundSecondary,
  });
  const mono = css({
    fontFamily: "monospace",
    fontSize: "11px",
    color: theme.colors.contentTertiary,
  });

  const panels = approvedSheet ? approvedSheet.panels : 0;

  return (
    <>
      <PageTitle
        meta={
          loading
            ? "Loading"
            : `${String(scenes.length)} scenes · ${String(inputs?.attempts ?? 0)} generations here`
        }
      >
        Scenes
      </PageTitle>
      <ParagraphXSmall>
        Pick the people, press generate, review what comes back. The master, the references and the
        scene&apos;s coverage prompt are resolved for you.
      </ParagraphXSmall>

      {error ? (
        <Notification
          kind={NOTIFICATION_KIND.negative}
          overrides={{ Body: { style: { width: "auto" } } }}
        >
          {error}
        </Notification>
      ) : null}
      {note ? (
        <Notification
          kind={NOTIFICATION_KIND.positive}
          overrides={{ Body: { style: { width: "auto" } } }}
        >
          {note}
        </Notification>
      ) : null}
      {inputs && !inputs.media_live ? (
        <Notification
          kind={NOTIFICATION_KIND.warning}
          overrides={{ Body: { style: { width: "auto" } } }}
        >
          Google media is off on this host, so the generate buttons will refuse rather than call
          anything.
        </Notification>
      ) : null}

      <div className={css({ display: "flex", gap: "6px", flexWrap: "wrap", margin: "12px 0" })}>
        {scenes.map((one) => (
          <Button
            key={one.scene_key}
            size={SIZE.compact}
            kind={one.scene_key === selected ? BUTTON_KIND.primary : BUTTON_KIND.secondary}
            onClick={() => {
              chooseScene(one.scene_key);
            }}
          >
            {one.scene_key}
            {one.approved_master_id ? null : (
              <span className={css({ marginLeft: "6px", opacity: 0.7 })}>no master</span>
            )}
          </Button>
        ))}
      </div>

      <SectionTitle>1 — The master, which is yours to choose</SectionTitle>
      <div
        className={css({
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
          gap: "10px",
          alignItems: "center",
          marginBottom: "16px",
        })}
      >
        <Input
          value={scene ? scene.scene_key : newScene}
          onChange={(event) => {
            setSelected(null);
            setNewScene(event.currentTarget.value);
          }}
          placeholder="Scene key, e.g. W01-P28"
        />
        <input ref={masterInput} type="file" accept="image/png,image/jpeg,image/webp" />
        <Checkbox
          checked={approveMasterOnUpload}
          onChange={(event) => {
            setApproveMasterOnUpload(event.currentTarget.checked);
          }}
        >
          Approve it
        </Checkbox>
        <Button disabled={busy !== null} onClick={onRegisterMaster}>
          Add master
        </Button>
      </div>

      {scene && scene.masters.length > 0 ? (
        <div
          className={css({
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
            gap: "12px",
            marginBottom: "24px",
          })}
        >
          {scene.masters.map((one) => (
            <div key={one.id} className={card}>
              <img
                src={previewSource(one.asset)}
                alt={`${scene.scene_key} master`}
                className={css({
                  width: "100%",
                  height: "120px",
                  objectFit: "contain",
                  background: theme.colors.backgroundTertiary,
                  borderRadius: "6px",
                })}
              />
              <div className={css({ display: "flex", gap: "4px", flexWrap: "wrap" })}>
                <Tag
                  closeable={false}
                  kind={one.status === "approved" ? TAG_KIND.positive : TAG_KIND.warning}
                  overrides={{ Text: { style: { maxWidth: "none" } } }}
                >
                  {one.status}
                </Tag>
                <Tag closeable={false} kind={TAG_KIND.neutral}>
                  {`${String(one.asset.width)}×${String(one.asset.height)}`}
                </Tag>
              </div>
              {one.status === "approved" ? null : (
                <Button
                  size={SIZE.mini}
                  disabled={busy !== null}
                  onClick={() =>
                    void act("approve-master", async () => {
                      await approveMaster(one.id, "Approved from the Scenes bench");
                      return "That is the master now. Everything below is built from it.";
                    })
                  }
                >
                  Use this one
                </Button>
              )}
            </div>
          ))}
        </div>
      ) : null}

      {master ? (
        <>
          <SectionTitle>2 — Who is in it</SectionTitle>
          {inputs?.source ? (
            <ParagraphXSmall>{`The coverage prompt comes from ${inputs.source}.`}</ParagraphXSmall>
          ) : (
            <>
              <ParagraphXSmall>
                This scene&apos;s key matches no prompt filename, so pick the one it uses. A scene
                named as its own canon names it will match without this.
              </ParagraphXSmall>
              <div
                className={css({ display: "flex", gap: "6px", flexWrap: "wrap", margin: "8px 0" })}
              >
                {(inputs?.available_prompts ?? []).map((choice) => (
                  <Button
                    key={choice.name}
                    size={SIZE.mini}
                    kind={promptName === choice.name ? BUTTON_KIND.primary : BUTTON_KIND.secondary}
                    onClick={() => {
                      setPromptName(choice.name);
                    }}
                  >
                    {`${choice.name} · ${String(choice.characters)} chars`}
                  </Button>
                ))}
              </div>
            </>
          )}
          <div className={css({ display: "flex", gap: "6px", flexWrap: "wrap", margin: "10px 0" })}>
            {(inputs?.references ?? []).map((reference) => {
              const on = picked.has(reference.key);
              return (
                <Button
                  key={reference.key}
                  size={SIZE.mini}
                  kind={on ? BUTTON_KIND.primary : BUTTON_KIND.secondary}
                  onClick={() => {
                    const next = new Set(picked);
                    if (on) next.delete(reference.key);
                    else next.add(reference.key);
                    setPicked(next);
                  }}
                >
                  {`${reference.slug} · ${reference.role.replace(/_/g, " ")}`}
                </Button>
              );
            })}
          </div>
          <ParagraphXSmall>
            {`${String(new Set([...picked].map((one) => one.split(":")[0])).size)} people selected. Nano holds identity for five; send only who the panels need.`}
          </ParagraphXSmall>
          <Button
            disabled={busy !== null || (!inputs?.prompt && promptName === null)}
            isLoading={busy === "sheet"}
            onClick={onGenerate}
          >
            Generate coverage sheet
          </Button>

          <div className={css({ marginTop: "24px" })}>
            <SectionTitle>3 — The sheet</SectionTitle>
          </div>
          <div
            className={css({
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(230px, 1fr))",
              gap: "12px",
              marginBottom: "20px",
            })}
          >
            {sheets.map((sheet) => (
              <div key={sheet.id} className={card}>
                <img
                  src={previewSource(sheet.asset)}
                  alt={sheet.label}
                  className={css({
                    width: "100%",
                    height: "190px",
                    objectFit: "contain",
                    background: theme.colors.backgroundTertiary,
                    borderRadius: "6px",
                  })}
                />
                <div className={css({ display: "flex", gap: "4px", flexWrap: "wrap" })}>
                  <Tag
                    closeable={false}
                    kind={
                      sheet.status === "approved"
                        ? TAG_KIND.positive
                        : sheet.status === "candidate"
                          ? TAG_KIND.warning
                          : TAG_KIND.neutral
                    }
                    overrides={{ Text: { style: { maxWidth: "none" } } }}
                  >
                    {sheet.status}
                  </Tag>
                  <Tag closeable={false} kind={TAG_KIND.neutral}>
                    {`${String(sheet.rows)}×${String(sheet.columns)}`}
                  </Tag>
                  <Tag closeable={false} kind={TAG_KIND.neutral}>
                    {`${String(sheet.reference_asset_ids.length)} refs`}
                  </Tag>
                </div>
                <LabelSmall className={mono}>{shortSha(sheet.asset.sha256)}</LabelSmall>
                {sheet.status === "approved" ? null : (
                  <div className={css({ display: "flex", gap: "6px", flexWrap: "wrap" })}>
                    <Button
                      size={SIZE.mini}
                      disabled={busy !== null}
                      onClick={() =>
                        void act("approve-sheet", async () => {
                          await approveContactSheet(sheet.id, "Approved from the Scenes bench");
                          return "Panels are chosen from that sheet now.";
                        })
                      }
                    >
                      Approve
                    </Button>
                    <Button
                      size={SIZE.mini}
                      kind={BUTTON_KIND.tertiary}
                      disabled={busy !== null}
                      onClick={() =>
                        void act("reject-sheet", async () => {
                          await rejectTake(sheet.asset.id, "Rejected from the Scenes bench");
                          return "Rejected and kept. Generate another when you are ready.";
                        })
                      }
                    >
                      Reject
                    </Button>
                  </div>
                )}
              </div>
            ))}
          </div>
          {sheets.length === 0 ? (
            <ParagraphXSmall>Nothing generated yet for this master.</ParagraphXSmall>
          ) : null}

          {approvedSheet ? (
            <>
              <SectionTitle>4 — Panels</SectionTitle>
              <ParagraphXSmall>
                Each panel goes back to Nano on its own and comes back as a standalone still.
              </ParagraphXSmall>
              <div
                className={css({
                  display: "grid",
                  gridTemplateColumns: `repeat(${String(approvedSheet.columns)}, minmax(150px, 1fr))`,
                  gap: "12px",
                  marginTop: "12px",
                })}
              >
                {Array.from({ length: panels }, (_, index) => index + 1).map((panel) => {
                  const frame = frameByPanel.get(panel);
                  return (
                    <div key={panel} className={card}>
                      {frame ? (
                        <img
                          src={previewSource(frame.asset)}
                          alt={frame.name}
                          className={css({
                            width: "100%",
                            height: "200px",
                            objectFit: "contain",
                            background: theme.colors.backgroundTertiary,
                            borderRadius: "6px",
                          })}
                        />
                      ) : (
                        <div
                          className={css({
                            height: "200px",
                            display: "grid",
                            placeItems: "center",
                            background: theme.colors.backgroundTertiary,
                            borderRadius: "6px",
                            color: theme.colors.contentTertiary,
                            fontSize: "28px",
                          })}
                        >
                          {panel}
                        </div>
                      )}
                      {frame ? (
                        <>
                          <div className={css({ display: "flex", gap: "4px", flexWrap: "wrap" })}>
                            <Tag
                              closeable={false}
                              kind={TAG_KIND.neutral}
                              overrides={{ Text: { style: { maxWidth: "none" } } }}
                            >
                              {frame.name}
                            </Tag>
                            <Tag
                              closeable={false}
                              kind={frame.approved_for_veo ? TAG_KIND.positive : TAG_KIND.warning}
                              overrides={{ Text: { style: { maxWidth: "none" } } }}
                            >
                              {frame.approved_for_veo ? "ready for Veo" : "pending"}
                            </Tag>
                          </div>
                          <div className={css({ display: "flex", gap: "6px", flexWrap: "wrap" })}>
                            {frame.approved_for_veo ? (
                              <Button
                                size={SIZE.mini}
                                isLoading={busy === `animate-${frame.name}`}
                                disabled={busy !== null}
                                onClick={() => {
                                  onAnimate(frame.name);
                                }}
                              >
                                Animate
                              </Button>
                            ) : (
                              <Button
                                size={SIZE.mini}
                                disabled={busy !== null}
                                onClick={() =>
                                  void act("approve-panel", async () => {
                                    await approveCoverage(frame.id, "Approved on the bench");
                                    return `${frame.name} can be animated.`;
                                  })
                                }
                              >
                                Approve
                              </Button>
                            )}
                            <Button
                              size={SIZE.mini}
                              kind={BUTTON_KIND.tertiary}
                              isLoading={busy === `panel-${String(panel)}`}
                              disabled={busy !== null}
                              onClick={() => {
                                onExtract(panel);
                              }}
                            >
                              Redo
                            </Button>
                          </div>
                        </>
                      ) : (
                        <>
                          <Input
                            size={SIZE.mini}
                            value={shotNames[panel] ?? ""}
                            onChange={(event) => {
                              setShotNames({
                                ...shotNames,
                                [panel]: event.currentTarget.value,
                              });
                            }}
                            placeholder={`panel-${String(panel)}`}
                          />
                          <Button
                            size={SIZE.mini}
                            isLoading={busy === `panel-${String(panel)}`}
                            disabled={busy !== null}
                            onClick={() => {
                              onExtract(panel);
                            }}
                          >
                            Extract
                          </Button>
                        </>
                      )}
                    </div>
                  );
                })}
              </div>
            </>
          ) : (
            <ParagraphXSmall>
              Approve a sheet and its nine panels appear here, each with its own extract button.
            </ParagraphXSmall>
          )}

          <SectionTitle>5 — Takes</SectionTitle>
          <ParagraphXSmall>
            An approved panel becomes a Veo first frame. Six seconds are generated and one and a
            half to four survive, so a shot collects takes: watch one, type the seconds worth
            cutting, and keep it. Rejected takes stay on the list — they are what the prompt cost.
          </ParagraphXSmall>
          <Textarea
            value={motionPrompt}
            onChange={(event) => {
              setMotionEdit(event.currentTarget.value);
            }}
            placeholder="Motion direction"
            rows={4}
          />
          <ParagraphXSmall>
            {inputs?.motion_prompt
              ? "Read from this scene's own shot specification. Edit it per shot; what is sent is what is recorded."
              : "This scene has no shot specification holding motion direction, so type it here."}
          </ParagraphXSmall>

          {takes.length === 0 ? (
            <ParagraphXSmall>
              No takes yet. Animate an approved panel above and the first one lands here.
            </ParagraphXSmall>
          ) : (
            [...takesByShot.entries()].map(([shot, shotTakes]) => (
              <div key={shot} className={css({ marginTop: "14px" })}>
                <LabelSmall>{shot}</LabelSmall>
                <div
                  className={css({
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
                    gap: "12px",
                    marginTop: "8px",
                  })}
                >
                  {shotTakes.map((take) => {
                    const range = ranges[take.id] ?? { from: "", to: "" };
                    return (
                      <div key={take.id} className={card}>
                        <video
                          src={takeVideoSource(take.id)}
                          controls
                          preload="metadata"
                          className={css({
                            width: "100%",
                            borderRadius: "6px",
                            background: theme.colors.backgroundTertiary,
                          })}
                        />
                        <div className={css({ display: "flex", gap: "4px", flexWrap: "wrap" })}>
                          <Tag
                            closeable={false}
                            kind={TAG_KIND.neutral}
                            overrides={{ Text: { style: { maxWidth: "none" } } }}
                          >
                            attempt {take.attempt}
                          </Tag>
                          <Tag
                            closeable={false}
                            kind={
                              take.status === "keeper"
                                ? TAG_KIND.positive
                                : take.status === "rejected"
                                  ? TAG_KIND.negative
                                  : TAG_KIND.warning
                            }
                            overrides={{ Text: { style: { maxWidth: "none" } } }}
                          >
                            {take.status}
                          </Tag>
                          {take.video.has_audio ? (
                            <Tag
                              closeable={false}
                              kind={TAG_KIND.warning}
                              overrides={{ Text: { style: { maxWidth: "none" } } }}
                            >
                              still has sound
                            </Tag>
                          ) : null}
                          {take.stale ? (
                            <Tag
                              closeable={false}
                              kind={TAG_KIND.negative}
                              overrides={{ Text: { style: { maxWidth: "none" } } }}
                            >
                              shot re-extracted since
                            </Tag>
                          ) : null}
                        </div>
                        <div className={mono}>
                          {seconds(take.video.duration_ms)} ·{" "}
                          {take.video.width && take.video.height
                            ? `${String(take.video.width)}×${String(take.video.height)}`
                            : "size unknown"}{" "}
                          · {shortSha(take.video.sha256)}
                        </div>
                        {take.keeper_from_ms !== null || take.keeper_to_ms !== null ? (
                          <div className={mono}>
                            keeper {take.keeper_from_ms ?? 0}–{take.keeper_to_ms ?? "end"}ms
                          </div>
                        ) : null}
                        {take.status === "rejected" ? null : (
                          <>
                            <div className={css({ display: "flex", gap: "6px" })}>
                              <Input
                                size={SIZE.mini}
                                value={range.from}
                                onChange={(event) => {
                                  setRanges({
                                    ...ranges,
                                    [take.id]: { ...range, from: event.currentTarget.value },
                                  });
                                }}
                                placeholder="from ms"
                              />
                              <Input
                                size={SIZE.mini}
                                value={range.to}
                                onChange={(event) => {
                                  setRanges({
                                    ...ranges,
                                    [take.id]: { ...range, to: event.currentTarget.value },
                                  });
                                }}
                                placeholder="to ms"
                              />
                            </div>
                            <div className={css({ display: "flex", gap: "6px", flexWrap: "wrap" })}>
                              <Button
                                size={SIZE.mini}
                                isLoading={busy === `keep-${take.id}`}
                                disabled={busy !== null}
                                onClick={() => {
                                  onKeep(take);
                                }}
                              >
                                Keep
                              </Button>
                              <Button
                                size={SIZE.mini}
                                kind={BUTTON_KIND.tertiary}
                                disabled={busy !== null}
                                onClick={() =>
                                  void act(`reject-${take.id}`, async () => {
                                    await rejectMotionTake(take.id, "Rejected on the bench");
                                    return "Rejected and kept. Animate again for the next attempt.";
                                  })
                                }
                              >
                                Reject
                              </Button>
                              <Button
                                size={SIZE.mini}
                                kind={BUTTON_KIND.tertiary}
                                isLoading={busy === `animate-${take.shot}`}
                                disabled={busy !== null}
                                onClick={() => {
                                  onAnimate(take.shot);
                                }}
                              >
                                Redo
                              </Button>
                            </div>
                          </>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))
          )}
        </>
      ) : scene ? (
        <ParagraphXSmall>Approve a master and the rest of the pipeline opens up.</ParagraphXSmall>
      ) : null}
    </>
  );
}

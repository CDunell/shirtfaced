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
 * The screen is built one row per person, not one per photograph. Each person
 * has three references and only one of them is normally sent — the 3x3 contact
 * sheet, which already contains the other two as cells 1 and 5. Listing all
 * thirty-three was a wall of near-identical chips that argued for sending the
 * same view three times. The singles are still reachable behind Frames.
 *
 * Approve and reject are both real. Rejecting keeps the take: a rerun is a new
 * call, never an overwrite, and a bad take is evidence about the prompt.
 *
 * Motion is deliberately absent. NANO_BANANA_VEO_SCENE_PRODUCTION_PIPELINE.md
 * §17 records the Veo route that already exists and is proven: a trigger under
 * studio/veo-coverage-triggers/ runs the workflow, which resolves the seed by
 * checksum, generates, strips the generated audio that §20 requires stripping,
 * probes and checksums the result. A second route built here would be a second
 * answer to a solved question, so this bench ends at an approved standalone
 * shot and hands over there.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useStyletron } from "baseui";
import { Button, KIND as BUTTON_KIND, SIZE } from "baseui/button";
import { Checkbox } from "baseui/checkbox";
import { Input } from "baseui/input";
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
  animateCoverage,
  generateSheet,
  previewSource,
  registerMaster,
  rejectContactSheet,
  type ContactSheet,
  type CoverageFrame,
  type PanelPlanEntry,
  takeSource,
  type PipelineInputs,
  type ReferenceChoice,
  type Scene,
} from "../api/production";

/** What the coverage prompt asked panel N to be, if it numbered its observations. */
function plannedFor(sheet: ContactSheet | null, panel: number): PanelPlanEntry | null {
  return sheet?.panel_plan.find((entry) => entry.panel === panel) ?? null;
}

/** The planned title as a shot name, or the panel number when there is no plan. */
function plannedName(sheet: ContactSheet | null, panel: number): string {
  const planned = plannedFor(sheet, panel);
  if (!planned) return `panel-${String(panel)}`;
  return (
    planned.title
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "")
      .slice(0, 96) || `panel-${String(panel)}`
  );
}

/**
 * Pick the extraction that belongs to the current panel plan, never whichever
 * historical row happens to sort last.
 *
 * Rejected/superseded sheets are deliberately kept as production history, so a
 * master can hold more than one extraction carrying the same panel number. The
 * normal re-extraction loop moves the planned shot name onto the replacement
 * sheet. If legacy rows make a panel ambiguous and none has the planned name,
 * show no frame rather than offering Approve on pixels whose lineage is wrong.
 */
function currentFrameForPanel(
  frames: CoverageFrame[],
  sheet: ContactSheet | null,
  panel: number,
): CoverageFrame | null {
  const matches = frames.filter((one) => one.panel === panel);
  if (matches.length === 0) return null;
  const planned = plannedName(sheet, panel);
  // Never fall back to an arbitrary historical extraction just because it is the
  // only row carrying this panel number. The current sheet owns the shot name;
  // until that exact shot has been extracted, Stage 4 must show Extract.
  return matches.find((one) => one.name === planned) ?? null;
}

function shortSha(sha: string): string {
  return sha.slice(0, 12);
}

/** The one reference a person is normally sent: their 3x3 sheet. */
function defaultReference(choices: ReferenceChoice[]): ReferenceChoice | null {
  return (
    choices.find((one) => one.role === "contact_sheet") ??
    choices.find((one) => one.role === "head_shoulders_neutral") ??
    choices[0] ??
    null
  );
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
  const [showFrames, setShowFrames] = useState(false);
  // A thumbnail is 120-200px of a 4K sheet. Judging a panel means looking at
  // it, and every review in this pipeline is somebody looking at an image.
  const [zoom, setZoom] = useState<{ src: string; alt: string } | null>(null);
  // Bumped after a generation so the <video> re-fetches instead of showing
  // the previous take from cache.
  const [takes, setTakes] = useState<Record<string, number>>({});
  const [showUpload, setShowUpload] = useState(false);
  const [promptName, setPromptName] = useState<string | null>(null);
  const [shotNames, setShotNames] = useState<Record<number, string>>({});

  const reload = useCallback(async (sceneKey: string | null) => {
    const data = await fetchScenes();
    setScenes(data);
    const key = sceneKey ?? data[0]?.scene_key ?? null;
    setInputs(key ? await fetchPipelineInputs(key) : null);
    return key;
  }, []);

  useEffect(() => {
    fetchScenes()
      .then(async (data) => {
        setScenes(data);
        const key = data[0]?.scene_key ?? null;
        setSelected(key);
        if (key) setInputs(await fetchPipelineInputs(key));
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

  const scene = useMemo(
    () => scenes.find((one) => one.scene_key === selected) ?? null,
    [scenes, selected],
  );
  // Memoised because onExtract closes over the approved sheet to name the panel
  // it is extracting, and a value re-derived every render defeats the callback.
  const master = useMemo(
    () => scene?.masters.find((one) => one.id === scene.approved_master_id) ?? null,
    [scene],
  );
  const sheets: ContactSheet[] = useMemo(() => master?.contact_sheets ?? [], [master]);
  const approvedSheet = useMemo(
    () => sheets.find((one) => one.status === "approved") ?? null,
    [sheets],
  );
  const frames: CoverageFrame[] = master?.coverage ?? [];

  const chooseScene = useCallback((key: string) => {
    setSelected(key);
    setNote(null);
    setPicked(new Set());
    void fetchPipelineInputs(key).then(setInputs);
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
      const name = (shotNames[panel] ?? plannedName(approvedSheet, panel)).trim();
      void act(`panel-${String(panel)}`, async () => {
        await extractPanel(scene.scene_key, { panel, name, selections: [...picked] });
        return `Panel ${String(panel)} came back as ${name}. Approve it to let Veo animate it.`;
      });
    },
    [act, approvedSheet, picked, scene, shotNames],
  );

  const people = useMemo(() => {
    const grouped = new Map<string, ReferenceChoice[]>();
    for (const one of inputs?.references ?? [])
      grouped.set(one.slug, [...(grouped.get(one.slug) ?? []), one]);
    return [...grouped.entries()];
  }, [inputs]);

  const togglePerson = useCallback(
    (choices: ReferenceChoice[]) => {
      const keys = choices.map((one) => one.key);
      const next = new Set(picked);
      if (keys.some((key) => next.has(key))) for (const key of keys) next.delete(key);
      else {
        const chosen = defaultReference(choices);
        if (chosen) next.add(chosen.key);
      }
      setPicked(next);
    },
    [picked],
  );

  const card = css({
    border: `1px solid ${theme.colors.borderOpaque}`,
    borderRadius: "10px",
    padding: "10px",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    background: theme.colors.backgroundSecondary,
  });
  const row = css({
    display: "flex",
    alignItems: "center",
    gap: "10px",
    flexWrap: "wrap",
    marginTop: "20px",
  });
  const quiet = css({ color: theme.colors.contentTertiary });
  const mono = css({
    fontFamily: "monospace",
    fontSize: "11px",
    color: theme.colors.contentTertiary,
  });

  const panels = approvedSheet ? approvedSheet.panels : 0;

  return (
    <>
      {/* Full size, on a dark ground, filling whatever screen it is on. Click
          anywhere or press Escape. A sheet is 3072px wide and the decision it
          exists for cannot be made at 190. */}
      {zoom ? (
        <div
          role="button"
          tabIndex={0}
          aria-label="Close the enlarged image"
          onClick={() => {
            setZoom(null);
          }}
          onKeyDown={(event) => {
            if (event.key === "Escape" || event.key === "Enter" || event.key === " ") setZoom(null);
          }}
          className={css({
            position: "fixed",
            inset: "0",
            zIndex: "80",
            background: "rgba(0,0,0,0.88)",
            display: "grid",
            placeItems: "center",
            padding: "16px",
            cursor: "zoom-out",
          })}
        >
          <img
            src={zoom.src}
            alt={zoom.alt}
            className={css({
              maxWidth: "100%",
              maxHeight: "100%",
              objectFit: "contain",
            })}
          />
        </div>
      ) : null}

      <PageTitle
        meta={
          loading
            ? "Loading"
            : `${String(scenes.length)} scenes · ${String(inputs?.attempts ?? 0)} generations here`
        }
      >
        Scenes
      </PageTitle>
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

      <div className={row}>
        <SectionTitle>1 — Master</SectionTitle>
        {master ? (
          <Button
            size={SIZE.mini}
            kind={BUTTON_KIND.tertiary}
            onClick={() => {
              setShowUpload(!showUpload);
            }}
          >
            {showUpload ? "Cancel" : "Add another"}
          </Button>
        ) : null}
      </div>

      {/* Hidden once a scene has one: on a phone this was four controls above
          the fold, in front of the master they came to look at. */}
      {master && !showUpload ? null : (
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
      )}

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
                onClick={() => {
                  setZoom({ src: previewSource(one.asset), alt: `${scene.scene_key} master` });
                }}
                className={css({
                  width: "100%",
                  height: "120px",
                  objectFit: "contain",
                  background: theme.colors.backgroundTertiary,
                  borderRadius: "6px",
                  cursor: "zoom-in",
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
          <div className={row}>
            <SectionTitle>2 — Who is in it</SectionTitle>
            <Button
              size={SIZE.mini}
              kind={showFrames ? BUTTON_KIND.primary : BUTTON_KIND.tertiary}
              onClick={() => {
                setShowFrames(!showFrames);
              }}
            >
              Frames
            </Button>
          </div>
          {inputs?.source ? null : (
            <>
              <ParagraphXSmall>
                No prompt is filed under this scene&apos;s name. Pick the one it uses.
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
            {people.map(([slug, choices]) => {
              const chosen = choices.filter((one) => picked.has(one.key));
              return (
                <Button
                  key={slug}
                  size={SIZE.compact}
                  kind={chosen.length > 0 ? BUTTON_KIND.primary : BUTTON_KIND.secondary}
                  onClick={() => {
                    togglePerson(choices);
                  }}
                >
                  {slug}
                  {showFrames && chosen.length > 0 ? (
                    <span className={css({ marginLeft: "6px", opacity: 0.7 })}>
                      {String(chosen.length)}
                    </span>
                  ) : null}
                </Button>
              );
            })}
          </div>

          {/* The individual frames, for the rare panel that wants one on its
              own. Cells 1 and 5 of the sheet the person button already sends. */}
          {showFrames ? (
            <div
              className={css({ display: "flex", gap: "6px", flexWrap: "wrap", margin: "0 0 10px" })}
            >
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
          ) : null}

          <div className={row}>
            <Button
              disabled={busy !== null || (!inputs?.prompt && promptName === null)}
              isLoading={busy === "sheet"}
              onClick={onGenerate}
            >
              Generate coverage sheet
            </Button>
            <LabelSmall className={quiet}>
              {`${String(new Set([...picked].map((one) => one.split(":")[0])).size)} of 5`}
            </LabelSmall>
          </div>

          <div className={css({ marginTop: "24px" })}>
            <SectionTitle>3 — Sheet</SectionTitle>
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
                  onClick={() => {
                    setZoom({ src: previewSource(sheet.asset), alt: sheet.label });
                  }}
                  className={css({
                    width: "100%",
                    height: "190px",
                    objectFit: "contain",
                    background: theme.colors.backgroundTertiary,
                    borderRadius: "6px",
                    cursor: "zoom-in",
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
                          await rejectContactSheet(sheet.id, "Rejected from the Scenes bench");
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
              <div
                className={css({
                  display: "grid",
                  gridTemplateColumns: `repeat(${String(approvedSheet.columns)}, minmax(150px, 1fr))`,
                  gap: "12px",
                  marginTop: "12px",
                })}
              >
                {Array.from({ length: panels }, (_, index) => index + 1).map((panel) => {
                  const frame = currentFrameForPanel(frames, approvedSheet, panel);
                  return (
                    <div key={panel} className={card}>
                      {frame ? (
                        <img
                          src={previewSource(frame.asset)}
                          alt={frame.name}
                          onClick={() => {
                            setZoom({ src: previewSource(frame.asset), alt: frame.name });
                          }}
                          className={css({
                            width: "100%",
                            height: "200px",
                            objectFit: "contain",
                            background: theme.colors.backgroundTertiary,
                            borderRadius: "6px",
                            cursor: "zoom-in",
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
                      {plannedFor(approvedSheet, panel) ? (
                        <LabelSmall>{plannedFor(approvedSheet, panel)?.title}</LabelSmall>
                      ) : null}
                      {frame ? null : <div />}
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
                          {frame.approved_for_veo && takes[frame.id] ? (
                            <video
                              src={`${takeSource(frame.id)}?v=${String(takes[frame.id])}`}
                              controls
                              preload="metadata"
                              className={css({
                                width: "100%",
                                borderRadius: "6px",
                                background: theme.colors.backgroundTertiary,
                              })}
                            />
                          ) : null}
                          <div className={css({ display: "flex", gap: "6px", flexWrap: "wrap" })}>
                            {frame.approved_for_veo ? (
                              <Button
                                size={SIZE.mini}
                                isLoading={busy === `animate-${frame.id}`}
                                disabled={busy !== null}
                                onClick={() =>
                                  void act(`animate-${frame.id}`, async () => {
                                    const take = await animateCoverage(frame.id);
                                    setTakes({ ...takes, [frame.id]: Date.now() });
                                    const length =
                                      take.duration_seconds === null
                                        ? "unknown length"
                                        : `${take.duration_seconds.toFixed(1)}s`;
                                    return `${take.shot}: ${length}${take.has_audio ? ", AUDIO NOT STRIPPED" : ", silent"}.`;
                                  })
                                }
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
                            placeholder={plannedName(approvedSheet, panel)}
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
            <ParagraphXSmall>Approve a sheet and its panels appear here.</ParagraphXSmall>
          )}
        </>
      ) : scene ? (
        <ParagraphXSmall>Approve a master and the rest of the pipeline opens up.</ParagraphXSmall>
      ) : null}
    </>
  );
}

/**
 * Scene masters, the coverage sheet chosen from them, and the shots extracted.
 *
 * The order on screen is the order of the contract in
 * NANO_BANANA_CONTACT_SHEET_PIPELINE.md: an approved master, then one approved
 * 3x3 coverage sheet, then a standalone still per panel, then approval for
 * motion. Each stage is refused until the one above it exists, and the refusal
 * says which stage is missing rather than greying a button out silently.
 *
 * The deterministic crop is still here, at the bottom, behind a disclosure.
 * §8 supersedes it for the Nano route and not everywhere, but leading with it
 * would point at the wrong pipeline.
 *
 * What this shows that a directory could not: that a master is a candidate,
 * that a sheet has been superseded so its panel numbers no longer mean what
 * they meant, and that a shot was taken from a master that has since changed.
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
  cutCoverage,
  fetchScenes,
  previewSource,
  recordPanel,
  registerContactSheet,
  registerMaster,
  type ContactSheet,
  type CoverageFrame,
  type Scene,
} from "../api/production";

function shortSha(sha: string): string {
  return sha.slice(0, 12);
}

export function ScenesBench(): React.JSX.Element {
  const [css, theme] = useStyletron();
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const [newScene, setNewScene] = useState("");
  const [approveMasterOnUpload, setApproveMasterOnUpload] = useState(false);
  const masterInput = useRef<HTMLInputElement>(null);

  const [sheetLabel, setSheetLabel] = useState("");
  const [sheetReferences, setSheetReferences] = useState("");
  const [approveSheetOnUpload, setApproveSheetOnUpload] = useState(false);
  const sheetInput = useRef<HTMLInputElement>(null);

  const [panelNumber, setPanelNumber] = useState("1");
  const [panelName, setPanelName] = useState("");
  const panelInput = useRef<HTMLInputElement>(null);

  const [showCrop, setShowCrop] = useState(false);
  const [shotName, setShotName] = useState("");
  const [shotX, setShotX] = useState("0");

  useEffect(() => {
    const controller = new AbortController();
    fetchScenes(controller.signal)
      .then((data) => {
        setScenes(data);
        setSelected((current) => current ?? data[0]?.scene_key ?? null);
        setLoading(false);
      })
      .catch((cause: unknown) => {
        if (controller.signal.aborted) return;
        setError(cause instanceof ApiError ? cause.message : "Scenes are unavailable.");
        setLoading(false);
      });
    return () => {
      controller.abort();
    };
  }, []);

  const act = useCallback(async (work: () => Promise<string | null>) => {
    setBusy(true);
    setError(null);
    setNote(null);
    try {
      const message = await work();
      setScenes(await fetchScenes());
      if (message) setNote(message);
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "That did not go through.");
    } finally {
      setBusy(false);
    }
  }, []);

  const scene = useMemo(
    () => scenes.find((one) => one.scene_key === selected) ?? null,
    [scenes, selected],
  );
  const master = scene?.masters.find((one) => one.id === scene.approved_master_id) ?? null;
  const sheets: ContactSheet[] = master?.contact_sheets ?? [];
  const approvedSheet = sheets.find((one) => one.status === "approved") ?? null;
  const frames: CoverageFrame[] = master?.coverage ?? [];

  const onRegisterMaster = useCallback(() => {
    const file = masterInput.current?.files?.[0];
    const key = (scene?.scene_key ?? newScene).trim();
    if (!file || !key) return;

    void act(async () => {
      await registerMaster(key, file, { approve: approveMasterOnUpload });
      if (masterInput.current) masterInput.current.value = "";
      setSelected(key);
      setNewScene("");
      return approveMasterOnUpload
        ? `Approved as the master for ${key}.`
        : `Registered as a candidate for ${key}. Nothing resolves it until it is approved.`;
    });
  }, [act, approveMasterOnUpload, newScene, scene]);

  const onRegisterSheet = useCallback(() => {
    const file = sheetInput.current?.files?.[0];
    const label = sheetLabel.trim();
    if (!file || !scene || !label) return;

    void act(async () => {
      await registerContactSheet(scene.scene_key, file, {
        label,
        approve: approveSheetOnUpload,
        referenceAssetIds: sheetReferences
          .split(",")
          .map((one) => one.trim())
          .filter(Boolean),
      });
      if (sheetInput.current) sheetInput.current.value = "";
      setSheetLabel("");
      return approveSheetOnUpload
        ? "Approved. Panels are now chosen from this sheet."
        : "Registered as a candidate. Approve it before extracting panels.";
    });
  }, [act, approveSheetOnUpload, scene, sheetLabel, sheetReferences]);

  const onRecordPanel = useCallback(() => {
    const file = panelInput.current?.files?.[0];
    const name = panelName.trim();
    const panel = Number.parseInt(panelNumber, 10);
    if (!file || !scene || !name || Number.isNaN(panel)) return;

    void act(async () => {
      await recordPanel(scene.scene_key, file, { name, panel });
      if (panelInput.current) panelInput.current.value = "";
      setPanelName("");
      return `Panel ${String(panel)} recorded as ${name}. Not approved for motion yet.`;
    });
  }, [act, panelName, panelNumber, scene]);

  const onCut = useCallback(() => {
    const name = shotName.trim();
    const x = Number.parseInt(shotX, 10);
    if (!scene || !name || Number.isNaN(x)) return;

    void act(async () => {
      await cutCoverage(scene.scene_key, { name, x });
      setShotName("");
      return `Cut ${name} as a literal crop. Not approved for motion.`;
    });
  }, [act, scene, shotName, shotX]);

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
  const row = css({
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
    gap: "10px",
    alignItems: "center",
    marginBottom: "20px",
  });

  return (
    <>
      <PageTitle
        meta={
          loading
            ? "Loading"
            : `${String(scenes.length)} scenes · ${String(
                scenes.filter((one) => one.approved_master_id).length,
              )} with an approved master`
        }
      >
        Scenes
      </PageTitle>
      <ParagraphXSmall>
        Approved master, then one approved coverage sheet, then a standalone shot per panel. Veo
        reaches an approved shot of the current sheet and nothing else.
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

      <div className={css({ display: "flex", gap: "6px", flexWrap: "wrap", margin: "12px 0" })}>
        {scenes.map((one) => (
          <Button
            key={one.scene_key}
            size={SIZE.compact}
            kind={one.scene_key === selected ? BUTTON_KIND.primary : BUTTON_KIND.secondary}
            onClick={() => {
              setSelected(one.scene_key);
              setNote(null);
            }}
          >
            {one.scene_key}
            {one.approved_master_id ? null : (
              <span className={css({ marginLeft: "6px", opacity: 0.7 })}>no master</span>
            )}
          </Button>
        ))}
      </div>

      <SectionTitle>1 — Master</SectionTitle>
      <div className={row}>
        <Input
          value={scene ? scene.scene_key : newScene}
          onChange={(event) => {
            setSelected(null);
            setNewScene(event.currentTarget.value);
          }}
          placeholder="Scene key, e.g. pub-1105"
        />
        <input ref={masterInput} type="file" accept="image/png,image/jpeg,image/webp" />
        <Checkbox
          checked={approveMasterOnUpload}
          onChange={(event) => {
            setApproveMasterOnUpload(event.currentTarget.checked);
          }}
        >
          Approve as the master
        </Checkbox>
        <Button disabled={busy} onClick={onRegisterMaster}>
          Register master
        </Button>
      </div>

      {scene ? (
        <div
          className={css({
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(230px, 1fr))",
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
                  height: "140px",
                  objectFit: "contain",
                  background: theme.colors.backgroundTertiary,
                  borderRadius: "6px",
                })}
              />
              <div className={css({ display: "flex", gap: "4px", flexWrap: "wrap" })}>
                <Tag
                  closeable={false}
                  kind={
                    one.status === "approved"
                      ? TAG_KIND.positive
                      : one.status === "candidate"
                        ? TAG_KIND.warning
                        : TAG_KIND.neutral
                  }
                  overrides={{ Text: { style: { maxWidth: "none" } } }}
                >
                  {one.status}
                </Tag>
                <Tag closeable={false} kind={TAG_KIND.neutral}>
                  {`${String(one.asset.width)}×${String(one.asset.height)}`}
                </Tag>
              </div>
              <LabelSmall className={mono}>{shortSha(one.asset.sha256)}</LabelSmall>
              {one.status === "approved" ? null : (
                <Button
                  size={SIZE.mini}
                  disabled={busy}
                  onClick={() =>
                    void act(async () => {
                      await approveMaster(one.id, "Approved from the Scenes bench");
                      return `That is now the master for ${scene.scene_key}. Any previous one is superseded, and so are its sheets.`;
                    })
                  }
                >
                  Make this the master
                </Button>
              )}
            </div>
          ))}
        </div>
      ) : null}

      {master ? (
        <>
          <SectionTitle>2 — Coverage contact sheet</SectionTitle>
          <ParagraphXSmall>
            The 3×3 Nano sheet generated from this master plus the character references you fed it.
            Paste those reference asset IDs so the manifest is recorded, not remembered.
          </ParagraphXSmall>
          <div className={row}>
            <Input
              value={sheetLabel}
              onChange={(event) => {
                setSheetLabel(event.currentTarget.value);
              }}
              placeholder="Label, e.g. w01-p28-coverage"
            />
            <input ref={sheetInput} type="file" accept="image/png,image/jpeg,image/webp" />
            <Input
              value={sheetReferences}
              onChange={(event) => {
                setSheetReferences(event.currentTarget.value);
              }}
              placeholder="Reference asset IDs, comma separated"
            />
            <Checkbox
              checked={approveSheetOnUpload}
              onChange={(event) => {
                setApproveSheetOnUpload(event.currentTarget.checked);
              }}
            >
              Approve as the sheet
            </Checkbox>
            <Button disabled={busy || !sheetLabel.trim()} onClick={onRegisterSheet}>
              Register sheet
            </Button>
          </div>

          <div
            className={css({
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(230px, 1fr))",
              gap: "12px",
              marginBottom: "24px",
            })}
          >
            {sheets.map((sheet) => (
              <div key={sheet.id} className={card}>
                <img
                  src={previewSource(sheet.asset)}
                  alt={sheet.label}
                  className={css({
                    width: "100%",
                    height: "200px",
                    objectFit: "contain",
                    background: theme.colors.backgroundTertiary,
                    borderRadius: "6px",
                  })}
                />
                <div className={css({ display: "flex", gap: "4px", flexWrap: "wrap" })}>
                  <Tag
                    closeable={false}
                    kind={TAG_KIND.neutral}
                    overrides={{ Text: { style: { maxWidth: "none" } } }}
                  >
                    {sheet.label}
                  </Tag>
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
                </div>
                <ParagraphXSmall className={css({ margin: 0 })}>
                  {sheet.reference_asset_ids.length > 0
                    ? `${String(sheet.reference_asset_ids.length)} character reference(s) recorded`
                    : "No character references recorded"}
                </ParagraphXSmall>
                <LabelSmall className={mono}>{shortSha(sheet.asset.sha256)}</LabelSmall>
                {sheet.status === "approved" ? null : (
                  <Button
                    size={SIZE.mini}
                    disabled={busy}
                    onClick={() =>
                      void act(async () => {
                        await approveContactSheet(sheet.id, "Approved from the Scenes bench");
                        return "Panels are now chosen from that sheet.";
                      })
                    }
                  >
                    Make this the sheet
                  </Button>
                )}
              </div>
            ))}
          </div>
          {sheets.length === 0 ? (
            <ParagraphXSmall>
              No sheet yet. Generate one from this master and the approved character references,
              then register it here.
            </ParagraphXSmall>
          ) : null}

          <SectionTitle>3 — Shots</SectionTitle>
          {approvedSheet ? (
            <>
              <ParagraphXSmall>
                {`Record the standalone still Nano returned for a panel. Panels 1–${String(
                  approvedSheet.panels,
                )} on ${approvedSheet.label}.`}
              </ParagraphXSmall>
              <div className={row}>
                <Input
                  value={panelNumber}
                  onChange={(event) => {
                    setPanelNumber(event.currentTarget.value);
                  }}
                  placeholder="Panel number"
                />
                <Input
                  value={panelName}
                  onChange={(event) => {
                    setPanelName(event.currentTarget.value);
                  }}
                  placeholder="Shot name, e.g. damo-wide"
                />
                <input ref={panelInput} type="file" accept="image/png,image/jpeg,image/webp" />
                <Button disabled={busy || !panelName.trim()} onClick={onRecordPanel}>
                  Record panel
                </Button>
              </div>
            </>
          ) : (
            <ParagraphXSmall>
              No approved sheet, so there are no panels to record against. Approve one above.
            </ParagraphXSmall>
          )}

          <div
            className={css({
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
              gap: "12px",
            })}
          >
            {frames.map((frame) => (
              <div key={frame.id} className={card}>
                <img
                  src={previewSource(frame.asset)}
                  alt={frame.name}
                  className={css({
                    width: "100%",
                    height: "230px",
                    objectFit: "contain",
                    background: theme.colors.backgroundTertiary,
                    borderRadius: "6px",
                  })}
                />
                <div className={css({ display: "flex", gap: "4px", flexWrap: "wrap" })}>
                  <Tag
                    closeable={false}
                    kind={TAG_KIND.neutral}
                    overrides={{ Text: { style: { maxWidth: "none" } } }}
                  >
                    {frame.name}
                  </Tag>
                  {frame.panel === null ? (
                    <Tag closeable={false} kind={TAG_KIND.neutral}>
                      crop
                    </Tag>
                  ) : (
                    <Tag closeable={false} kind={TAG_KIND.accent}>
                      {`panel ${String(frame.panel)}`}
                    </Tag>
                  )}
                  <Tag
                    closeable={false}
                    kind={frame.approved_for_veo ? TAG_KIND.positive : TAG_KIND.warning}
                    overrides={{ Text: { style: { maxWidth: "none" } } }}
                  >
                    {frame.approved_for_veo ? "approved for Veo" : "pending"}
                  </Tag>
                  {frame.stale ? (
                    <Tag
                      closeable={false}
                      kind={TAG_KIND.negative}
                      overrides={{ Text: { style: { maxWidth: "none" } } }}
                    >
                      master has changed
                    </Tag>
                  ) : null}
                </div>
                <ParagraphXSmall className={css({ margin: 0 })}>
                  {frame.width !== null && frame.height !== null
                    ? `${String(frame.width)}×${String(frame.height)}`
                    : "dimensions unknown"}
                </ParagraphXSmall>
                <LabelSmall className={mono}>{shortSha(frame.frame_sha256)}</LabelSmall>
                {frame.approved_for_veo ? null : (
                  <Button
                    size={SIZE.mini}
                    disabled={busy}
                    onClick={() =>
                      void act(async () => {
                        await approveCoverage(frame.id, "Approved from the Scenes bench");
                        return `${frame.name} can be animated.`;
                      })
                    }
                  >
                    Approve for Veo
                  </Button>
                )}
              </div>
            ))}
          </div>
          {frames.length === 0 ? <ParagraphXSmall>No shots yet.</ParagraphXSmall> : null}

          <div className={css({ marginTop: "28px" })}>
            <Button
              size={SIZE.mini}
              kind={BUTTON_KIND.tertiary}
              onClick={() => {
                setShowCrop((current) => !current);
              }}
            >
              {showCrop ? "Hide" : "Show"} the deterministic crop route
            </Button>
            {showCrop ? (
              <>
                <ParagraphXSmall>
                  Superseded for the Nano path, and still the cheapest way to take an exact
                  observation out of an image nobody needs to regenerate. Offset is in the
                  master&apos;s own pixels; it is {String(master.asset.width)}px wide.
                </ParagraphXSmall>
                <div className={row}>
                  <Input
                    value={shotName}
                    onChange={(event) => {
                      setShotName(event.currentTarget.value);
                    }}
                    placeholder="Shot name"
                  />
                  <Input
                    value={shotX}
                    onChange={(event) => {
                      setShotX(event.currentTarget.value);
                    }}
                    placeholder="x offset"
                  />
                  <Button
                    size={SIZE.compact}
                    kind={BUTTON_KIND.secondary}
                    disabled={busy || !shotName.trim()}
                    onClick={onCut}
                  >
                    Cut 9:16 crop
                  </Button>
                </div>
              </>
            ) : null}
          </div>
        </>
      ) : scene ? (
        <ParagraphXSmall>
          No approved master for this scene, so there is nothing to cover yet.
        </ParagraphXSmall>
      ) : null}
    </>
  );
}

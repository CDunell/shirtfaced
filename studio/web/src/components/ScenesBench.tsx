/**
 * Scene masters and the coverage cut from them.
 *
 * Two decisions gate every paid Veo run: which image is the scene's master, and
 * which 9:16 frames may be animated. Both were reachable only over SSH until
 * this screen existed, which is a poor place to keep a decision that costs
 * money to get wrong.
 *
 * What it shows that a directory could not: that a master is a candidate rather
 * than approved, that approving a second one supersedes the first, and that a
 * coverage frame was cut from a master that has since been replaced — the
 * failure that already happened once here, silently.
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
  approveCoverage,
  approveMaster,
  cutCoverage,
  fetchScenes,
  previewSource,
  registerMaster,
  type Scene,
  type SceneMaster,
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
  const [approveOnUpload, setApproveOnUpload] = useState(false);
  const masterInput = useRef<HTMLInputElement>(null);

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
  const approved = scene?.masters.find((one) => one.id === scene.approved_master_id) ?? null;

  const onRegister = useCallback(() => {
    const file = masterInput.current?.files?.[0];
    const key = (scene?.scene_key ?? newScene).trim();
    if (!file || !key) return;

    void act(async () => {
      await registerMaster(key, file, { approve: approveOnUpload });
      if (masterInput.current) masterInput.current.value = "";
      setSelected(key);
      setNewScene("");
      return approveOnUpload
        ? `Approved as the master for ${key}.`
        : `Registered as a candidate for ${key}. Nothing resolves it until it is approved.`;
    });
  }, [act, approveOnUpload, newScene, scene]);

  const onCut = useCallback(() => {
    const name = shotName.trim();
    const x = Number.parseInt(shotX, 10);
    if (!scene || !name || Number.isNaN(x)) return;

    void act(async () => {
      await cutCoverage(scene.scene_key, { name, x });
      setShotName("");
      return `Cut ${name}. Not approved for Veo — cutting is not approving.`;
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

  const frames = approved?.coverage ?? [];

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
        One approved master per scene, and the 9:16 coverage cut from it. Veo can only reach an
        approved frame of the current master.
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

      <SectionTitle>Register a master</SectionTitle>
      <div
        className={css({
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "10px",
          alignItems: "center",
          marginBottom: "24px",
        })}
      >
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
          checked={approveOnUpload}
          onChange={(event) => {
            setApproveOnUpload(event.currentTarget.checked);
          }}
        >
          Approve as the master
        </Checkbox>
        <Button disabled={busy} onClick={onRegister}>
          Register
        </Button>
      </div>

      {scene ? (
        <>
          <SectionTitle>{`${scene.scene_key} — masters`}</SectionTitle>
          <div
            className={css({
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
              gap: "12px",
              marginBottom: "24px",
            })}
          >
            {scene.masters.map((master: SceneMaster) => (
              <div key={master.id} className={card}>
                <img
                  src={previewSource(master.asset)}
                  alt={`${scene.scene_key} master`}
                  className={css({
                    width: "100%",
                    height: "160px",
                    objectFit: "contain",
                    background: theme.colors.backgroundTertiary,
                    borderRadius: "6px",
                  })}
                />
                <div className={css({ display: "flex", gap: "4px", flexWrap: "wrap" })}>
                  <Tag
                    closeable={false}
                    kind={
                      master.status === "approved"
                        ? TAG_KIND.positive
                        : master.status === "candidate"
                          ? TAG_KIND.warning
                          : TAG_KIND.neutral
                    }
                    overrides={{ Text: { style: { maxWidth: "none" } } }}
                  >
                    {master.status}
                  </Tag>
                  <Tag closeable={false} kind={TAG_KIND.neutral}>
                    {`${String(master.asset.width)}×${String(master.asset.height)}`}
                  </Tag>
                </div>
                <LabelSmall className={mono}>{shortSha(master.asset.sha256)}</LabelSmall>
                {master.status === "approved" ? null : (
                  <Button
                    size={SIZE.mini}
                    disabled={busy}
                    onClick={() =>
                      void act(async () => {
                        await approveMaster(master.id, "Approved from the Scenes bench");
                        return `That is now the master for ${scene.scene_key}. Any previous one is superseded.`;
                      })
                    }
                  >
                    Make this the master
                  </Button>
                )}
              </div>
            ))}
          </div>

          <SectionTitle>Coverage</SectionTitle>
          {approved ? (
            <>
              <div
                className={css({
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
                  gap: "10px",
                  alignItems: "center",
                  marginBottom: "16px",
                })}
              >
                <Input
                  value={shotName}
                  onChange={(event) => {
                    setShotName(event.currentTarget.value);
                  }}
                  placeholder="Shot name, e.g. pub-1105-a"
                />
                <Input
                  value={shotX}
                  onChange={(event) => {
                    setShotX(event.currentTarget.value);
                  }}
                  placeholder="x offset in master pixels"
                />
                <Button disabled={busy || !shotName.trim()} onClick={onCut}>
                  Cut 9:16 frame
                </Button>
                <ParagraphXSmall className={css({ margin: 0 })}>
                  {`Master is ${String(approved.asset.width)}px wide.`}
                </ParagraphXSmall>
              </div>

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
                        height: "240px",
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
                      <Tag
                        closeable={false}
                        kind={frame.approved_for_veo ? TAG_KIND.positive : TAG_KIND.warning}
                      >
                        {frame.approved_for_veo ? "approved for Veo" : "pending"}
                      </Tag>
                      {frame.stale ? (
                        <Tag
                          closeable={false}
                          kind={TAG_KIND.negative}
                          overrides={{ Text: { style: { maxWidth: "none" } } }}
                        >
                          cut from a superseded master
                        </Tag>
                      ) : null}
                    </div>
                    <ParagraphXSmall className={css({ margin: 0 })}>
                      {`${String(frame.width)}×${String(frame.height)} at x=${String(frame.x)}`}
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
              {frames.length === 0 ? (
                <ParagraphXSmall>
                  No coverage yet. Cut a frame above; the offset is measured in the master&apos;s
                  own pixels.
                </ParagraphXSmall>
              ) : null}
            </>
          ) : (
            <ParagraphXSmall>
              No approved master, so nothing can be cut. Approve one above first.
            </ParagraphXSmall>
          )}
        </>
      ) : null}
    </>
  );
}

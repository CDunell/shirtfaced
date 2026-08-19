import { useCallback, useEffect, useState } from "react";
import { useStyletron } from "baseui";
import { Button, KIND as BUTTON_KIND, SIZE } from "baseui/button";
import { Notification, KIND as NOTIFICATION_KIND } from "baseui/notification";
import { Tag, KIND as TAG_KIND } from "baseui/tag";
import { ParagraphSmall, ParagraphXSmall } from "baseui/typography";

import { ApiError } from "../api/client";
import {
  analyseRoughCut,
  fetchRoughCut,
  renderRoughCut,
  roughCutSource,
  updateRoughCutShot,
  type RoughCutShot,
  type RoughCutState,
} from "../api/sceneShots";

function displayName(name: string): string {
  return name
    .split("-")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function decisionKind(decision: RoughCutShot["decision"]) {
  if (decision === "keep") return TAG_KIND.positive;
  if (decision === "reject") return TAG_KIND.negative;
  return TAG_KIND.warning;
}

export function RoughCutPanel({ sceneKey }: { sceneKey: string }): React.JSX.Element {
  const [css, theme] = useStyletron();
  const [state, setState] = useState<RoughCutState | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [videoVersion, setVideoVersion] = useState(0);

  const load = useCallback(async () => {
    setState(await fetchRoughCut(sceneKey));
  }, [sceneKey]);

  useEffect(() => {
    void load().catch((cause: unknown) => {
      setError(cause instanceof ApiError ? cause.message : "Rough cut state is unavailable.");
    });
  }, [load]);

  const run = useCallback(async (key: string, work: () => Promise<RoughCutState>, message: string) => {
    setBusy(key);
    setError(null);
    setNote(null);
    try {
      const next = await work();
      setState(next);
      setNote(message);
      if (next.output_exists) setVideoVersion((value) => value + 1);
    } catch (cause: unknown) {
      setError(cause instanceof ApiError ? cause.message : "That did not go through.");
    } finally {
      setBusy(null);
    }
  }, []);

  const patch = useCallback(async (
    shot: RoughCutShot,
    values: Partial<Pick<RoughCutShot, "decision" | "in_seconds" | "out_seconds">>,
  ) => {
    await run(
      `edit-${shot.shot_id}`,
      () => updateRoughCutShot(sceneKey, shot.shot_id, values),
      `${displayName(shot.shot_name)} edit updated.`,
    );
  }, [run, sceneKey]);

  const panel = css({
    border: `1px solid ${theme.colors.borderOpaque}`,
    borderRadius: "14px",
    padding: "14px",
    backgroundColor: theme.colors.backgroundSecondary,
  });
  const row = css({
    display: "grid",
    gridTemplateColumns: "minmax(140px, 1fr) auto auto minmax(220px, 2fr)",
    gap: "10px",
    alignItems: "center",
    padding: "10px 0",
    borderTop: `1px solid ${theme.colors.borderOpaque}`,
    "@media screen and (max-width: 820px)": { gridTemplateColumns: "1fr" },
  });
  const numberInput = css({
    width: "76px",
    padding: "7px 8px",
    borderRadius: "7px",
    border: `1px solid ${theme.colors.borderOpaque}`,
    backgroundColor: theme.colors.inputFill,
    color: theme.colors.contentPrimary,
  });

  return (
    <section className={css({ marginTop: "22px" })}>
      <div className={css({ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "12px", flexWrap: "wrap", marginBottom: "8px" })}>
        <div>
          <strong>AI rough cut</strong>
          <ParagraphXSmall margin={0}>
            Scores the latest Veo take for each approved shot, picks a clean 1–3 second window, strips generated audio and assembles one 9:16 MP4.
          </ParagraphXSmall>
        </div>
        <div className={css({ display: "flex", gap: "8px", flexWrap: "wrap" })}>
          <Button
            size={SIZE.compact}
            kind={BUTTON_KIND.secondary}
            isLoading={busy === "analyse"}
            onClick={() => void run("analyse", () => analyseRoughCut(sceneKey), "AI analysis complete. Review the selections below.")}
          >
            {state?.shots.length ? "Re-analyse takes" : "Analyse takes"}
          </Button>
          <Button
            size={SIZE.compact}
            disabled={!state?.shots.some((shot) => shot.decision === "keep")}
            isLoading={busy === "render"}
            onClick={() => void run("render", () => renderRoughCut(sceneKey), "Rough cut built.")}
          >
            Build rough cut
          </Button>
        </div>
      </div>

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

      {state?.shots.length ? (
        <div className={panel}>
          {state.shots.map((shot) => (
            <div key={shot.shot_id} className={row}>
              <div>
                <strong>{displayName(shot.shot_name)}</strong>
                <ParagraphXSmall margin={0}>Take {shot.take_stamp}</ParagraphXSmall>
              </div>
              <Tag closeable={false} kind={decisionKind(shot.decision)}>{shot.decision}</Tag>
              <div className={css({ display: "flex", gap: "6px", alignItems: "center", flexWrap: "wrap" })}>
                <label>
                  <span className={css({ fontSize: "11px", display: "block" })}>In</span>
                  <input
                    className={numberInput}
                    type="number"
                    min="0"
                    step="0.1"
                    defaultValue={shot.in_seconds}
                    onBlur={(event) => {
                      const value = Number(event.currentTarget.value);
                      if (Number.isFinite(value) && value !== shot.in_seconds) void patch(shot, { in_seconds: value });
                    }}
                  />
                </label>
                <label>
                  <span className={css({ fontSize: "11px", display: "block" })}>Out</span>
                  <input
                    className={numberInput}
                    type="number"
                    min="0"
                    step="0.1"
                    defaultValue={shot.out_seconds}
                    onBlur={(event) => {
                      const value = Number(event.currentTarget.value);
                      if (Number.isFinite(value) && value !== shot.out_seconds) void patch(shot, { out_seconds: value });
                    }}
                  />
                </label>
              </div>
              <div>
                <ParagraphXSmall margin={0}>{shot.rationale}</ParagraphXSmall>
                <ParagraphXSmall margin={0}>
                  Identity {shot.identity_score}/5 · clean anatomy {shot.deformation_score}/5 · continuity {shot.continuity_score}/5 · world {shot.world_score}/5 · energy {shot.energy_score}/5
                </ParagraphXSmall>
                <div className={css({ display: "flex", gap: "5px", marginTop: "6px", flexWrap: "wrap" })}>
                  {(["keep", "maybe", "reject"] as const).map((decision) => (
                    <Button
                      key={decision}
                      size={SIZE.mini}
                      kind={shot.decision === decision ? BUTTON_KIND.primary : BUTTON_KIND.tertiary}
                      isLoading={busy === `edit-${shot.shot_id}`}
                      onClick={() => void patch(shot, { decision })}
                    >
                      {decision.charAt(0).toUpperCase() + decision.slice(1)}
                    </Button>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <ParagraphSmall>No edit analysis yet. Analyse takes after the production Veo shots are ready.</ParagraphSmall>
      )}

      {state?.output_exists ? (
        <div className={css({ marginTop: "14px", maxWidth: "420px" })}>
          <video
            key={videoVersion}
            src={`${roughCutSource(sceneKey)}?v=${String(videoVersion)}`}
            controls
            playsInline
            preload="metadata"
            className={css({ width: "100%", borderRadius: "12px", background: "#000" })}
          />
          <ParagraphXSmall marginTop="4px">Silent rough cut. Audio bed comes later.</ParagraphXSmall>
        </div>
      ) : null}
    </section>
  );
}

import { useCallback, useEffect, useRef, useState } from "react";
import { Button, Notification, ParagraphSmall, ParagraphXSmall, Tag, type TagKind } from "./ui";

import { ApiError } from "../api/client";
import {
  analyseRoughCut,
  fetchRoughCut,
  renderRoughCut,
  renderRoughCutFinal,
  roughCutAudioSource,
  roughCutFinalSource,
  roughCutSource,
  updateRoughCutAudio,
  updateRoughCutShot,
  uploadRoughCutAudio,
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

function decisionKind(decision: RoughCutShot["decision"]): TagKind {
  if (decision === "keep") return "positive";
  if (decision === "reject") return "negative";
  return "warning";
}

const panelClass = "rounded-[14px] border border-ink/10 bg-paper-2 p-3.5";
const rowClass =
  "grid grid-cols-[minmax(140px,1fr)_auto_auto_minmax(220px,2fr)] items-center gap-2.5 border-t border-ink/10 py-2.5 max-[820px]:grid-cols-1";
const numberInputClass =
  "w-[82px] rounded-[7px] border border-ink/15 bg-white px-2 py-[7px] text-ink";

export function RoughCutPanel({ sceneKey }: { sceneKey: string }): React.JSX.Element {
  const [state, setState] = useState<RoughCutState | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [videoVersion, setVideoVersion] = useState(0);
  const [finalVersion, setFinalVersion] = useState(0);
  const audioRef = useRef<HTMLInputElement>(null);

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
      if (next.final_exists) setFinalVersion((value) => value + 1);
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

  return (
    <section className="mt-[22px]">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-3">
        <div>
          <strong>AI rough cut</strong>
          <ParagraphXSmall>
            Scores the latest Veo take for each approved shot, picks a clean 1–3 second window, strips generated audio and assembles one 9:16 MP4.
          </ParagraphXSmall>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            size="compact"
            variant="secondary"
            isLoading={busy === "analyse"}
            onClick={() => void run("analyse", () => analyseRoughCut(sceneKey), "AI analysis complete. Review the selections below.")}
          >
            {state?.shots.length ? "Re-analyse takes" : "Analyse takes"}
          </Button>
          <Button
            size="compact"
            disabled={!state?.shots.some((shot) => shot.decision === "keep")}
            isLoading={busy === "render"}
            onClick={() => void run("render", () => renderRoughCut(sceneKey), "Rough cut built.")}
          >
            Build rough cut
          </Button>
        </div>
      </div>

      {error ? <Notification kind="negative">{error}</Notification> : null}
      {note ? <Notification kind="positive">{note}</Notification> : null}

      {state?.shots.length ? (
        <div className={panelClass}>
          {state.shots.map((shot) => (
            <div key={shot.shot_id} className={rowClass}>
              <div>
                <strong>{displayName(shot.shot_name)}</strong>
                <ParagraphXSmall>Take {shot.take_stamp}</ParagraphXSmall>
              </div>
              <Tag kind={decisionKind(shot.decision)}>{shot.decision}</Tag>
              <div className="flex flex-wrap items-center gap-1.5">
                <label>
                  <span className="block text-[11px]">In</span>
                  <input
                    className={numberInputClass}
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
                  <span className="block text-[11px]">Out</span>
                  <input
                    className={numberInputClass}
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
                <ParagraphXSmall>{shot.rationale}</ParagraphXSmall>
                <ParagraphXSmall>
                  Identity {shot.identity_score}/5 · clean anatomy {shot.deformation_score}/5 · continuity {shot.continuity_score}/5 · world {shot.world_score}/5 · energy {shot.energy_score}/5
                </ParagraphXSmall>
                <div className="mt-1.5 flex flex-wrap gap-[5px]">
                  {(["keep", "maybe", "reject"] as const).map((decision) => (
                    <Button
                      key={decision}
                      size="compact"
                      variant={shot.decision === decision ? "primary" : "ghost"}
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
        <div className="mt-3.5 max-w-[420px]">
          <video
            key={videoVersion}
            src={`${roughCutSource(sceneKey)}?v=${String(videoVersion)}`}
            controls
            playsInline
            preload="metadata"
            className="w-full rounded-xl bg-black"
          />
          <ParagraphXSmall className="mt-1">Silent rough cut.</ParagraphXSmall>
        </div>
      ) : null}

      {state?.output_exists ? (
        <div className="mt-5">
          <strong>Audio</strong>
          <ParagraphXSmall className="mt-0.5">
            Use one rights-owned music bed. Veo audio stays removed.
          </ParagraphXSmall>
          <div className={panelClass}>
            <div className="flex flex-wrap items-center gap-2">
              <input ref={audioRef} type="file" accept="audio/*,.mp3,.wav,.flac,.m4a,.aif,.aiff,.ogg" />
              <Button
                size="compact"
                variant="secondary"
                isLoading={busy === "audio-upload"}
                onClick={() => {
                  const file = audioRef.current?.files?.[0];
                  if (!file) return;
                  void run(
                    "audio-upload",
                    () => uploadRoughCutAudio(sceneKey, file),
                    `${file.name}: audio attached.`,
                  ).then(() => {
                    if (audioRef.current) audioRef.current.value = "";
                  });
                }}
              >
                {state.audio ? "Replace track" : "Upload owned track"}
              </Button>
            </div>

            {state.audio ? (
              <div className="mt-3">
                <ParagraphSmall className="mb-1.5">
                  <strong>{state.audio.filename}</strong>
                  {state.audio.duration_seconds ? ` · ${state.audio.duration_seconds.toFixed(1)}s` : ""}
                </ParagraphSmall>
                <audio
                  src={`${roughCutAudioSource(sceneKey)}?asset=${encodeURIComponent(state.audio.asset_id)}`}
                  controls
                  preload="metadata"
                  className="w-full max-w-[520px]"
                />
                <div className="mt-2.5 flex flex-wrap items-end gap-3">
                  <label>
                    <span className="block text-[11px]">Track in-point (sec)</span>
                    <input
                      className={numberInputClass}
                      type="number"
                      min="0"
                      step="0.1"
                      defaultValue={state.audio.in_seconds}
                      onBlur={(event) => {
                        const value = Number(event.currentTarget.value);
                        if (!Number.isFinite(value) || value === state.audio?.in_seconds) return;
                        void run(
                          "audio-settings",
                          () => updateRoughCutAudio(sceneKey, { in_seconds: value }),
                          "Audio in-point updated.",
                        );
                      }}
                    />
                  </label>
                  <label>
                    <span className="block text-[11px]">Music gain (dB)</span>
                    <input
                      className={numberInputClass}
                      type="number"
                      min="-30"
                      max="6"
                      step="0.5"
                      defaultValue={state.audio.gain_db}
                      onBlur={(event) => {
                        const value = Number(event.currentTarget.value);
                        if (!Number.isFinite(value) || value === state.audio?.gain_db) return;
                        void run(
                          "audio-settings",
                          () => updateRoughCutAudio(sceneKey, { gain_db: value }),
                          "Music level updated.",
                        );
                      }}
                    />
                  </label>
                  <Button
                    size="compact"
                    isLoading={busy === "final"}
                    onClick={() => void run(
                      "final",
                      () => renderRoughCutFinal(sceneKey),
                      "Final video built with owned audio.",
                    )}
                  >
                    {state.final_exists ? "Rebuild final" : "Build final"}
                  </Button>
                </div>
              </div>
            ) : (
              <ParagraphXSmall>Upload the track once, then choose where in the song this 10-second edit starts.</ParagraphXSmall>
            )}
          </div>
        </div>
      ) : null}

      {state?.final_exists ? (
        <div className="mt-4 max-w-[420px]">
          <strong>Final</strong>
          <video
            key={finalVersion}
            src={`${roughCutFinalSource(sceneKey)}?v=${String(finalVersion)}`}
            controls
            playsInline
            preload="metadata"
            className="mt-2 w-full rounded-xl bg-black"
          />
        </div>
      ) : null}
    </section>
  );
}

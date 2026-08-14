/**
 * One attempt, from brief to approved version.
 *
 * The spine of the product pipeline, and the screen Phase 1 exists to build.
 * Everything an attempt needs is here in the order it is needed: the brief to
 * take away, the drop zone to bring artwork back to, the measurement, the
 * scorecard, and the decision.
 *
 * **There is no generate button, and that is the design.** Phase 0.1: the app
 * owns the brief, the record, the measurement, the judgement and the decision.
 * It does not own the pixels. Paid subscriptions already cover generation and
 * an API key bills separately, so artwork is made in ChatGPT, Gemini or Claude
 * and brought back. The screen says so in words rather than leaving a reader
 * hunting for a control that will never exist.
 *
 * **Every state says what to do next**, in a sentence the server composes
 * (`next_action.py`), because two screens phrasing the same situation
 * separately is how they end up disagreeing about it.
 *
 * **The scorecard is rendered, not restated.** Groups, gates, questions,
 * maximums and floors all come from `/api/concepts/rubric`. Writing thirteen
 * gate ids and nine maximums out again in TypeScript is the duplication the
 * 14 August port had to undo once already.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useStyletron } from "baseui";
import { Button, KIND as BUTTON_KIND, SIZE } from "baseui/button";
import { FormControl } from "baseui/form-control";
import { Input } from "baseui/input";
import { Notification, KIND as NOTIFICATION_KIND } from "baseui/notification";
import { Select, type Value } from "baseui/select";
import { Textarea } from "baseui/textarea";
import { ParagraphSmall, ParagraphXSmall } from "baseui/typography";

import { ApiError } from "../api/client";
import {
  abandonAttempt,
  approveDesignWithSpec,
  assetUrl,
  decideAttempt,
  fetchBriefPackage,
  fetchGarments,
  fetchReview,
  fetchRubric,
  measureAttempt,
  printedVersionUrl,
  recordBriefTaken,
  saveReview,
  submitAttempt,
  uploadAsset,
  type BriefPackage,
  type CategoryAnswer,
  type ConceptDetailView,
  type DesignAttemptView,
  type DesignDecisionKind,
  type GateAnswer,
  type ReviewResult,
  type ReviewView,
  type Rubric,
  type Zone,
} from "../api/concepts";
import { SectionTitle } from "./chrome";
import { CORAL, INK, LIME, PAPER } from "../tokens";

function describe(cause: unknown): string {
  if (cause instanceof ApiError) return cause.message;
  return cause instanceof Error ? cause.message : String(cause);
}

const RESULTS: { id: ReviewResult; label: string }[] = [
  { id: "pass", label: "Pass" },
  { id: "fail", label: "Fail" },
  { id: "not_tested", label: "Not answered" },
];

export interface AttemptPanelProps {
  concept: ConceptDetailView;
  attempt: DesignAttemptView;
  /** The name against every decision. Owned by the bench, shared by both. */
  actor: string;
  onChanged: () => Promise<void> | void;
}

export function AttemptPanel({
  concept,
  attempt,
  actor,
  onChanged,
}: AttemptPanelProps): React.JSX.Element {
  const [css, theme] = useStyletron();
  const [rubric, setRubric] = useState<Rubric | null>(null);
  const [review, setReview] = useState<ReviewView | null>(null);
  const [garments, setGarments] = useState<Record<string, Zone[]>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const [dragging, setDragging] = useState(false);
  const [copied, setCopied] = useState(false);
  const fileInput = useRef<HTMLInputElement | null>(null);

  // The print spec, decided at approval because a raster carries no
  // millimetres. Nothing here is guessed from the file.
  const [garment, setGarment] = useState<Value>([]);
  const [zone, setZone] = useState<Value>([]);
  const [printWidth, setPrintWidth] = useState("");

  const load = useCallback(async () => {
    try {
      const [fetchedRubric, fetchedReview] = await Promise.all([
        fetchRubric(),
        fetchReview(attempt.id),
      ]);
      setRubric(fetchedRubric);
      setReview(fetchedReview);
    } catch (cause) {
      setError(describe(cause));
    }
  }, [attempt.id]);

  // Deferred a tick for the same reason DesignsBench defers its refresh: the
  // lint rule reads a synchronous call in an effect body as a cascading
  // render, and the fetch is genuinely external synchronisation.
  useEffect(() => {
    const timer = setTimeout(() => {
      void load();
    }, 0);
    return () => {
      clearTimeout(timer);
    };
  }, [load]);

  useEffect(() => {
    fetchGarments()
      .then(setGarments)
      .catch(() => {
        // An empty garment list is a state, not a failure: it means no garment
        // SVGs are present. The approval form says so rather than erroring.
        setGarments({});
      });
  }, []);

  const artwork = useMemo(
    () => attempt.assets.find((asset) => asset.kind === "artwork") ?? attempt.assets[0],
    [attempt.assets],
  );

  const version = useMemo(
    () => concept.versions.find((item) => item.design_attempt_id === attempt.id),
    [concept.versions, attempt.id],
  );

  // Composed on the server, so the words taken away and the record of what was
  // taken cannot differ -- and so the evidence travels with them. Phase 6.
  const [brief, setBrief] = useState<BriefPackage | null>(null);
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchBriefPackage(attempt.id)
        .then(setBrief)
        .catch(() => {
          setBrief(null);
        });
    }, 0);
    return () => {
      clearTimeout(timer);
    };
  }, [attempt.id]);

  const run = useCallback(
    async (label: string, work: () => Promise<unknown>) => {
      setBusy(label);
      setError(null);
      try {
        await work();
        await load();
        await onChanged();
      } catch (cause) {
        setError(describe(cause));
      } finally {
        setBusy(null);
      }
    },
    [load, onChanged],
  );

  const onFile = useCallback(
    (file: File) => {
      void run("upload", () => uploadAsset(attempt.id, file));
    },
    [attempt.id, run],
  );

  const answerGate = useCallback(
    (gateId: string, result: ReviewResult) => {
      if (!review) return;
      const gates: GateAnswer[] = review.gates.map((gate) => ({
        id: gate.id,
        result: gate.id === gateId ? result : gate.result,
        evidence: gate.evidence,
      }));
      void run("review", () => saveReview(attempt.id, actor || "owner", gates, ratings(review)));
    },
    [review, attempt.id, actor, run],
  );

  const rateCategory = useCallback(
    (categoryId: string, rating: number) => {
      if (!review || !rubric) return;
      const existing = ratings(review).filter((item) => item.id !== categoryId);
      const categories = [...existing, { id: categoryId, rating }];
      void run("review", () =>
        saveReview(attempt.id, actor || "owner", answers(review), categories),
      );
    },
    [review, rubric, attempt.id, actor, run],
  );

  /** The current 0-5 rating for a category, derived back from its points. */
  const ratingOf = useCallback(
    (categoryId: string): number | null => {
      const rated = review?.categories.find((item) => item.id === categoryId);
      if (!rated || rated.maximum <= 0) return null;
      return Math.round((rated.score / rated.maximum) * 5);
    },
    [review],
  );

  const evaluation = review?.evaluation;
  const sentence = review?.next_action ?? "";

  const metaLine = css({
    fontSize: "12px",
    fontWeight: 600,
    letterSpacing: "0.04em",
    textTransform: "uppercase",
    color: theme.colors.contentTertiary,
  });

  const panel = css({
    border: `1px solid ${theme.colors.backgroundSecondary}`,
    borderRadius: "16px",
    padding: "16px",
    marginBottom: "16px",
  });

  return (
    <div data-testid="attempt-panel">
      {/* The next action, first and unmissable. A person who has never used
          the tool should be able to read this and act without being told
          which screen they are on. */}
      <section
        className={css({
          backgroundColor: INK,
          color: PAPER,
          borderRadius: "16px",
          padding: "16px 18px",
          marginBottom: "16px",
        })}
      >
        <span
          className={css({
            display: "block",
            fontSize: "11px",
            fontWeight: 700,
            letterSpacing: "0.12em",
            textTransform: "uppercase",
            color: LIME,
            marginBottom: "6px",
          })}
        >
          Do this next
        </span>
        <p className={css({ margin: 0, fontSize: "15px", lineHeight: 1.5 })}>
          {sentence || "Loading the attempt…"}
        </p>
      </section>

      {error ? (
        <Notification
          kind={NOTIFICATION_KIND.negative}
          overrides={{ Body: { style: { width: "auto" } } }}
        >
          {error}
        </Notification>
      ) : null}

      {/* --- The brief, to take to a paid interface -------------------- */}
      <div className={panel}>
        <SectionTitle>Brief</SectionTitle>
        <pre
          className={css({
            whiteSpace: "pre-wrap",
            fontFamily: "inherit",
            fontSize: "13px",
            lineHeight: 1.55,
            margin: "0 0 10px",
            color: theme.colors.contentPrimary,
          })}
        >
          {brief?.text ?? "Composing the brief…"}
        </pre>
        {brief && brief.evidence_count > 0 ? (
          <ParagraphXSmall color={theme.colors.contentTertiary} marginTop={0}>
            {brief.evidence_count} evidence image
            {brief.evidence_count === 1 ? "" : "s"} travel with this brief. Attach them alongside it
            — they are what the era is read from.
          </ParagraphXSmall>
        ) : null}
        {attempt.method === "image_generation" ? (
          <ParagraphXSmall color={theme.colors.contentTertiary} marginTop={0}>
            This attempt carries a researched prompt. Copy the brief, paste it into a paid
            interface, and bring the image back below.
          </ParagraphXSmall>
        ) : null}
        <Button
          size={SIZE.compact}
          kind={BUTTON_KIND.secondary}
          disabled={!brief}
          onClick={() => {
            if (!brief) return;
            void navigator.clipboard.writeText(brief.text).then(
              () => {
                setCopied(true);
                setTimeout(() => {
                  setCopied(false);
                }, 2000);
              },
              () => {
                setError("The clipboard is not available. Select the brief and copy it.");
              },
            );
            // What went out, and when. The surviving half of Phase 6's original
            // exit test now that there is no generator here to send it to.
            void recordBriefTaken(attempt.id).catch(() => undefined);
          }}
        >
          {copied ? "Copied" : "Copy brief"}
        </Button>
      </div>

      {/* --- Artwork ---------------------------------------------------- */}
      <div className={panel}>
        <SectionTitle>Artwork</SectionTitle>
        {artwork ? (
          <div
            className={css({
              background: "#101010",
              borderRadius: "12px",
              padding: "12px",
              marginBottom: "10px",
              display: "flex",
              justifyContent: "center",
            })}
          >
            <img
              src={assetUrl(artwork.id)}
              alt={`attempt ${String(attempt.attempt_number)} artwork`}
              className={css({ maxWidth: "100%", maxHeight: "260px" })}
            />
          </div>
        ) : null}

        {review?.frozen ? null : (
          <div
            onDragOver={(event) => {
              event.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => {
              setDragging(false);
            }}
            onDrop={(event) => {
              event.preventDefault();
              setDragging(false);
              const file = event.dataTransfer.files[0];
              if (file) onFile(file);
            }}
            onClick={() => fileInput.current?.click()}
            className={css({
              border: `2px dashed ${dragging ? LIME : theme.colors.backgroundSecondary}`,
              borderRadius: "12px",
              padding: "22px",
              textAlign: "center",
              cursor: "pointer",
              backgroundColor: dragging ? theme.colors.backgroundSecondary : "transparent",
            })}
          >
            <ParagraphSmall marginTop={0} marginBottom={0}>
              {busy === "upload"
                ? "Storing the artwork…"
                : artwork
                  ? "Drop a replacement, or click to choose one."
                  : "Drop the artwork here, or click to choose a file."}
            </ParagraphSmall>
            <input
              ref={fileInput}
              type="file"
              accept="image/*,.svg"
              aria-label="Attach artwork to this attempt"
              className={css({ display: "none" })}
              onChange={(event) => {
                const file = event.currentTarget.files?.[0];
                if (file) onFile(file);
                event.currentTarget.value = "";
              }}
            />
          </div>
        )}

        {artwork && !review?.frozen ? (
          <div className={css({ marginTop: "10px" })}>
            <Button
              size={SIZE.compact}
              kind={BUTTON_KIND.secondary}
              disabled={busy !== null}
              onClick={() => {
                void run("measure", () => measureAttempt(attempt.id));
              }}
            >
              {busy === "measure" ? "Measuring…" : "Measure this artwork"}
            </Button>
            <ParagraphXSmall color={theme.colors.contentTertiary} marginBottom={0}>
              Measurement fills only what nobody has answered, and never overwrites a person&rsquo;s
              answer. It is the start of a review, not a verdict.
            </ParagraphXSmall>
          </div>
        ) : null}

        {review && Object.keys(review.measurements).length > 0 ? (
          <ParagraphXSmall color={theme.colors.contentSecondary}>
            Measured: {summarise(review.measurements)}
          </ParagraphXSmall>
        ) : null}
      </div>

      {/* --- The scorecard, in the constitution's three groups ---------- */}
      {rubric && review ? (
        <div className={panel}>
          <SectionTitle>Scorecard</SectionTitle>
          {evaluation ? <Verdict evaluation={evaluation} /> : null}

          {rubric.groups.map((group) => {
            const gates = rubric.gates.filter((gate) => gate.group === group.id);
            const categories = rubric.categories.filter((item) => item.group === group.id);
            return (
              <div key={group.id} className={css({ marginTop: "18px" })}>
                <h3
                  className={css({
                    fontSize: "15px",
                    fontWeight: 700,
                    margin: "0 0 2px",
                    color: theme.colors.contentPrimary,
                  })}
                >
                  {group.label}
                </h3>
                <ParagraphXSmall color={theme.colors.contentTertiary} marginTop={0}>
                  {group.blurb}
                </ParagraphXSmall>

                {gates.map((gate) => {
                  const answered = review.gates.find((item) => item.id === gate.id);
                  const result = answered?.result ?? "not_tested";
                  // The brief answers some gates as fact. They are shown with
                  // their evidence and never offered as a choice.
                  if (review.derived_gates.includes(gate.id)) {
                    return (
                      <div
                        key={gate.id}
                        className={css({
                          borderTop: `1px solid ${theme.colors.backgroundSecondary}`,
                          paddingTop: "10px",
                          marginTop: "10px",
                        })}
                      >
                        <ParagraphSmall marginTop={0} marginBottom="2px">
                          {gate.question}
                        </ParagraphSmall>
                        <ParagraphXSmall marginTop={0} marginBottom={0}>
                          <strong
                            className={css({
                              color: result === "pass" ? theme.colors.contentPrimary : CORAL,
                            })}
                          >
                            {result === "pass" ? "Pass" : "Fail"}
                          </strong>{" "}
                          — from the brief: {answered?.evidence ?? "not recorded"}
                        </ParagraphXSmall>
                      </div>
                    );
                  }
                  return (
                    <div
                      key={gate.id}
                      className={css({
                        borderTop: `1px solid ${theme.colors.backgroundSecondary}`,
                        paddingTop: "10px",
                        marginTop: "10px",
                      })}
                    >
                      <ParagraphSmall marginTop={0} marginBottom="6px">
                        {gate.question}
                      </ParagraphSmall>
                      <div className={css({ display: "flex", gap: "6px", flexWrap: "wrap" })}>
                        {RESULTS.map((option) => (
                          <button
                            key={option.id}
                            type="button"
                            disabled={review.frozen || busy !== null}
                            aria-pressed={result === option.id}
                            aria-label={`${gate.label}: ${option.label}`}
                            onClick={() => {
                              answerGate(gate.id, option.id);
                            }}
                            className={chip(
                              css,
                              theme,
                              result === option.id,
                              option.id === "fail" ? CORAL : undefined,
                            )}
                          >
                            {option.label}
                          </button>
                        ))}
                      </div>
                      {answered?.evidence ? (
                        <ParagraphXSmall color={theme.colors.contentTertiary} marginBottom={0}>
                          {answered.evidence}
                        </ParagraphXSmall>
                      ) : null}
                    </div>
                  );
                })}

                {categories.map((category) => {
                  const rating = ratingOf(category.id);
                  return (
                    <div
                      key={category.id}
                      className={css({
                        borderTop: `1px solid ${theme.colors.backgroundSecondary}`,
                        paddingTop: "10px",
                        marginTop: "10px",
                      })}
                    >
                      <ParagraphSmall marginTop={0} marginBottom="2px">
                        <strong>{category.label}</strong> — {category.prompt}
                      </ParagraphSmall>
                      <ParagraphXSmall color={theme.colors.contentTertiary} marginTop={0}>
                        {category.maximum} points. Release needs at least {category.ratingFloor}
                        /5.
                      </ParagraphXSmall>
                      <div className={css({ display: "flex", gap: "6px", flexWrap: "wrap" })}>
                        {[0, 1, 2, 3, 4, 5].map((value) => (
                          <button
                            key={value}
                            type="button"
                            disabled={review.frozen || busy !== null}
                            aria-pressed={rating === value}
                            aria-label={`${category.label}: ${String(value)} — ${
                              rubric.ratingMeanings[value] ?? ""
                            }`}
                            title={rubric.ratingMeanings[value] ?? ""}
                            onClick={() => {
                              rateCategory(category.id, value);
                            }}
                            className={chip(
                              css,
                              theme,
                              rating === value,
                              value < category.ratingFloor ? CORAL : undefined,
                            )}
                          >
                            {value}
                          </button>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>
      ) : null}

      {/* --- The decision ----------------------------------------------- */}
      {review?.frozen ? null : (
        <div className={panel}>
          <SectionTitle>Decision</SectionTitle>
          {/* One box, above both paths. Abandoning needs a reason as much as a
              rejection does, and a control that points at a field which is not
              on screen is worse than no instruction at all. */}
          <FormControl label="A note, a reason, or an instruction">
            <Textarea
              value={note}
              placeholder="Why, in your own words"
              onChange={(event) => {
                setNote(event.currentTarget.value);
              }}
            />
          </FormControl>

          {/* An attempt with no artwork has no other way out: decisions need
              something to look at. Kept beside Submit rather than hidden, so a
              row opened in error can be closed by whoever notices it. */}
          {attempt.state === "planned" ||
          attempt.state === "generating" ||
          attempt.state === "generated" ? (
            <div className={css({ marginBottom: "10px" })}>
              <Button
                size={SIZE.compact}
                kind={BUTTON_KIND.tertiary}
                disabled={busy !== null}
                onClick={() => {
                  const reason = note.trim();
                  if (!reason) {
                    setError(
                      "Say why this attempt is being abandoned. A row closed for no stated " +
                        "reason is just a gap.",
                    );
                    return;
                  }
                  void run("abandon", () => abandonAttempt(attempt.id, reason));
                }}
              >
                Abandon this attempt
              </Button>
              <ParagraphXSmall color={theme.colors.contentTertiary} marginBottom={0}>
                For a row that should not have been made — the wrong concept, a prompt that belongs
                to another idea. Put the reason in the box above; the row is kept.
              </ParagraphXSmall>
            </div>
          ) : null}

          {attempt.state === "generated" ? (
            <Button
              size={SIZE.compact}
              disabled={busy !== null}
              onClick={() => {
                void run("submit", () => submitAttempt(attempt.id));
              }}
            >
              Submit for a decision
            </Button>
          ) : null}

          {attempt.state === "awaiting_decision" ? (
            <>
              <div className={css({ display: "flex", gap: "6px", flexWrap: "wrap" })}>
                <Button
                  size={SIZE.compact}
                  disabled={busy !== null || !evaluation?.eligibleForDesignApproval}
                  title={
                    evaluation?.eligibleForDesignApproval
                      ? "The scorecard supports this"
                      : (evaluation?.blockers.join("; ") ?? "Answer the scorecard first")
                  }
                  onClick={() => {
                    void run("decide", () => decide(attempt.id, "approved", actor, note));
                  }}
                >
                  Approve
                </Button>
                <Button
                  size={SIZE.compact}
                  kind={BUTTON_KIND.secondary}
                  disabled={busy !== null}
                  onClick={() => {
                    void run("decide", () => decide(attempt.id, "rejected", actor, note));
                  }}
                >
                  Reject
                </Button>
                <Button
                  size={SIZE.compact}
                  kind={BUTTON_KIND.tertiary}
                  disabled={busy !== null}
                  onClick={() => {
                    void run("decide", () =>
                      decide(attempt.id, "variation_requested", actor, note),
                    );
                  }}
                >
                  Ask for a variation
                </Button>
              </div>
              {!evaluation?.eligibleForDesignApproval && evaluation ? (
                <ParagraphXSmall color={theme.colors.contentTertiary} marginBottom={0}>
                  Approve is unavailable until the scorecard supports it. Reject and variation are
                  always available — refusing something needs no rubric.
                </ParagraphXSmall>
              ) : null}
            </>
          ) : null}
        </div>
      )}

      {/* --- The version, and the print it enables ---------------------- */}
      {attempt.state === "approved" && !version ? (
        <div className={panel}>
          <SectionTitle>Record the approved version</SectionTitle>
          <ParagraphXSmall color={theme.colors.contentTertiary} marginTop={0}>
            Print needs all three. Artwork made in a paid interface comes back as pixels, and pixels
            have no physical size — so the print width is a decision recorded here, frozen with the
            approval.
          </ParagraphXSmall>
          {Object.keys(garments).length === 0 ? (
            <Notification kind={NOTIFICATION_KIND.warning}>
              No garment files are present, so there are no zones to choose. Add a garment SVG to
              assets/garments.
            </Notification>
          ) : null}
          <div
            className={css({
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
              gap: "10px",
            })}
          >
            <FormControl label="Garment">
              <Select
                options={Object.keys(garments).map((key) => ({ id: key, label: key }))}
                value={garment}
                placeholder="Choose a garment"
                onChange={(params) => {
                  setGarment(params.value);
                  setZone([]);
                }}
              />
            </FormControl>
            <FormControl label="Print zone">
              <Select
                options={(garments[String(garment[0]?.id ?? "")] ?? []).map((item) => ({
                  id: item.key,
                  label: `${item.key} — ${String(item.width_mm)}×${String(item.height_mm)}mm`,
                }))}
                value={zone}
                placeholder={garment.length ? "Choose a zone" : "Choose a garment first"}
                disabled={garment.length === 0}
                onChange={(params) => {
                  setZone(params.value);
                }}
              />
            </FormControl>
            <FormControl label="Print width (mm)">
              <Input
                value={printWidth}
                type="number"
                placeholder="240"
                onChange={(event) => {
                  setPrintWidth(event.currentTarget.value);
                }}
              />
            </FormControl>
          </div>
          <Button
            size={SIZE.compact}
            disabled={
              busy !== null ||
              garment.length === 0 ||
              zone.length === 0 ||
              !printWidth ||
              Number(printWidth) <= 0
            }
            onClick={() => {
              void run("approve", () =>
                approveDesignWithSpec(attempt.id, actor || "owner", {
                  garment_key: String(garment[0]?.id ?? ""),
                  zone_key: String(zone[0]?.id ?? ""),
                  print_width_mm: Number(printWidth),
                }),
              );
            }}
          >
            Record approved design v{concept.approved_versions + 1}
          </Button>
        </div>
      ) : null}

      {version ? (
        <div className={panel}>
          <SectionTitle>Printed</SectionTitle>
          <span className={metaLine}>
            v{version.version} · approved by {version.approved_by}
          </span>
          <div
            className={css({
              background: theme.colors.backgroundSecondary,
              borderRadius: "12px",
              padding: "12px",
              marginTop: "10px",
              display: "flex",
              justifyContent: "center",
            })}
          >
            <img
              src={printedVersionUrl(version.id)}
              alt={`version ${String(version.version)} printed on the garment`}
              className={css({ maxWidth: "100%", maxHeight: "420px" })}
            />
          </div>
        </div>
      ) : null}
    </div>
  );
}

/** The verdict, with the reasons it is not approvable spelled out. */
function Verdict({
  evaluation,
}: {
  evaluation: NonNullable<ReviewView["evaluation"]>;
}): React.JSX.Element {
  const [css, theme] = useStyletron();
  return (
    <div
      className={css({
        borderRadius: "12px",
        padding: "12px 14px",
        backgroundColor: theme.colors.backgroundSecondary,
        marginBottom: "10px",
      })}
    >
      <span
        className={css({
          fontSize: "22px",
          fontWeight: 700,
          color: theme.colors.contentPrimary,
        })}
      >
        {evaluation.percentage.toFixed(0)}/100
      </span>{" "}
      <span className={css({ fontSize: "13px", color: theme.colors.contentSecondary })}>
        {evaluation.bandLabel}
      </span>
      {evaluation.blockers.length > 0 ? (
        <ul
          className={css({
            margin: "8px 0 0",
            paddingLeft: "18px",
            fontSize: "13px",
            lineHeight: 1.5,
            color: theme.colors.contentSecondary,
          })}
        >
          {evaluation.blockers.map((blocker) => (
            <li key={blocker}>{blocker}</li>
          ))}
        </ul>
      ) : (
        <ParagraphXSmall marginBottom={0}>
          Every gate answered, every floor met. This design can be approved.
        </ParagraphXSmall>
      )}
    </div>
  );
}

/* --- helpers --------------------------------------------------------------- */

function answers(review: ReviewView): GateAnswer[] {
  return review.gates.map((gate) => ({
    id: gate.id,
    result: gate.result,
    evidence: gate.evidence,
  }));
}

/** Points back to the 0-5 rating the form works in. */
function ratings(review: ReviewView): CategoryAnswer[] {
  return review.categories
    .filter((item) => item.maximum > 0)
    .map((item) => ({
      id: item.id,
      rating: Math.round((item.score / item.maximum) * 5),
      notes: item.notes,
    }));
}

/** One note field, filed under the name the decision gives it: a rejection has
 * a reason, an approval has a note, a variation has an instruction. Empty is
 * omitted rather than sent as a blank string. */
function decide(
  attemptId: string,
  kind: DesignDecisionKind,
  actor: string,
  note: string,
): Promise<unknown> {
  const trimmed = note.trim();
  const words =
    trimmed === ""
      ? {}
      : kind === "rejected"
        ? { reason: trimmed }
        : kind === "variation_requested"
          ? { instruction: trimmed }
          : { note: trimmed };
  return decideAttempt(attemptId, kind, actor.trim() || "owner", words);
}

/** What was measured, in a line. Read defensively: the shape varies with what
 * could be measured, and a missing key is normal rather than an error. */
function summarise(measurements: Record<string, unknown>): string {
  const parts: string[] = [];
  const coverage = measurements.print_coverage;
  if (typeof coverage === "number") parts.push(`${(coverage * 100).toFixed(1)}% coverage`);
  const inks = measurements.ink_colours;
  if (typeof inks === "number") parts.push(`${String(inks)} ink colours`);
  for (const [key, label] of [
    ["thumbnail_survives", "thumbnail"],
    ["blur_survives", "blur"],
    ["greyscale_survives", "greyscale"],
  ] as const) {
    const value = measurements[key];
    if (typeof value === "boolean") parts.push(`${label} ${value ? "pass" : "fail"}`);
  }
  return parts.length ? parts.join(", ") : "nothing the image could answer";
}

type Css = ReturnType<typeof useStyletron>[0];
type Theme = ReturnType<typeof useStyletron>[1];

function chip(css: Css, theme: Theme, active: boolean, accent?: string): string {
  return css({
    appearance: "none",
    border: "none",
    cursor: "pointer",
    fontFamily: "inherit",
    fontSize: "12px",
    fontWeight: 700,
    letterSpacing: "0.03em",
    borderRadius: "999px",
    padding: "6px 12px",
    backgroundColor: active
      ? (accent ?? theme.colors.contentPrimary)
      : theme.colors.backgroundSecondary,
    color: active ? theme.colors.backgroundPrimary : theme.colors.contentSecondary,
    ":disabled": { cursor: "default", opacity: 0.6 },
  });
}

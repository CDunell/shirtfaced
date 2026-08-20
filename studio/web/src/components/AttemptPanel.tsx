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
import { Button, cx, FormControl, Input, Notification, ParagraphSmall, ParagraphXSmall, Select, Textarea } from "./ui";

function describe(cause: unknown): string {
  if (cause instanceof ApiError) return cause.message;
  return cause instanceof Error ? cause.message : String(cause);
}

const RESULTS: { id: ReviewResult; label: string }[] = [
  { id: "pass", label: "Pass" },
  { id: "fail", label: "Fail" },
  { id: "not_tested", label: "Not answered" },
];

const metaLine = "block text-[12px] font-semibold tracking-wide uppercase text-ink/50";

const panel = "mb-4 rounded-2xl border border-paper-2 p-4";

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
  const [rubric, setRubric] = useState<Rubric | null>(null);
  const [review, setReview] = useState<ReviewView | null>(null);
  const [garments, setGarments] = useState<Record<string, Zone[]>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const [dragging, setDragging] = useState(false);
  // Kept beside the drop zone as well as at the top of the panel.
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const fileInput = useRef<HTMLInputElement | null>(null);

  // The print spec, decided at approval because a raster carries no
  // millimetres. Nothing here is guessed from the file.
  const [garment, setGarment] = useState<string>("");
  const [zone, setZone] = useState<string>("");
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
      setUploadError(null);
      setBusy("upload");
      setError(null);
      uploadAsset(attempt.id, file)
        .then(async () => {
          await load();
          await onChanged();
        })
        .catch((cause: unknown) => {
          const message = describe(cause);
          setError(message);
          setUploadError(message);
        })
        .finally(() => {
          setBusy(null);
        });
    },
    [attempt.id, load, onChanged],
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

  // Settled means settled everywhere. `frozen` only covered a recorded
  // decision, so an abandoned attempt still offered a drop zone, a measure
  // button and a scorecard -- and the upload it invited came back 422 with the
  // error rendered at the top of the panel, out of sight of the control that
  // caused it. On a phone that reads as "nothing happened".
  const settled = review?.frozen === true || attempt.state === "failed";
  const evaluation = review?.evaluation;
  const sentence = review?.next_action ?? "";

  return (
    <div data-testid="attempt-panel">
      {/* The next action, first and unmissable. A person who has never used
          the tool should be able to read this and act without being told
          which screen they are on. */}
      <section className="mb-4 rounded-2xl bg-ink px-[18px] py-4 text-paper">
        <span className="mb-1.5 block text-[11px] font-bold tracking-[0.12em] text-lime uppercase">
          Do this next
        </span>
        <p className="m-0 text-[15px] leading-[1.5]">{sentence || "Loading the attempt…"}</p>
      </section>

      {error ? <Notification kind="negative">{error}</Notification> : null}

      {/* --- The brief, to take to a paid interface -------------------- */}
      <div className={panel}>
        <SectionTitle>Brief</SectionTitle>
        <pre className="mt-0 mb-2.5 font-inherit text-[13px] leading-[1.55] whitespace-pre-wrap text-ink">
          {brief?.text ?? "Composing the brief…"}
        </pre>
        {brief && brief.evidence_images.length > 0 ? (
          <>
            <ParagraphXSmall className="mt-0 text-ink/50">
              {brief.evidence_images.length} evidence image
              {brief.evidence_images.length === 1 ? "" : "s"} travel with this brief. Attach them
              alongside it — they are what the era is read from.
            </ParagraphXSmall>
            {/* Shown, not just counted. A count says evidence exists; the
                images say whether it is the right evidence, which is the only
                question worth asking of a reference. */}
            <div className="mb-2.5 grid grid-cols-[repeat(auto-fill,minmax(88px,1fr))] gap-2">
              {brief.evidence_images.map((image) => (
                <a
                  key={image.url}
                  href={image.url}
                  target="_blank"
                  rel="noreferrer"
                  title={`${image.filename} — listing ${image.listing_id}`}
                  className="block aspect-square overflow-hidden rounded-lg bg-paper-2"
                >
                  {/* Eager on purpose. `loading="lazy"` left all eight at
                      naturalWidth 0 when checked, and the panel is opened
                      deliberately by somebody who wants to look at exactly
                      these images -- deferring them buys nothing and is the
                      only thing standing between the reader and the evidence.
                      Eight thumbnails is not a payload worth optimising. */}
                  <img
                    src={image.url}
                    alt={`evidence ${image.filename} from listing ${image.listing_id}`}
                    className="h-full w-full object-cover"
                  />
                </a>
              ))}
            </div>
          </>
        ) : null}
        {attempt.method === "image_generation" ? (
          <ParagraphXSmall className="mt-0 text-ink/50">
            This attempt carries a researched prompt. Copy the brief, paste it into a paid
            interface, and bring the image back below.
          </ParagraphXSmall>
        ) : null}
        <Button
          size="compact"
          variant="secondary"
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
        {attempt.state === "failed" ? (
          <Notification kind="warning">
            This attempt was abandoned and cannot take artwork.
            {attempt.failure_message ? ` ${attempt.failure_message}` : ""}
          </Notification>
        ) : null}

        {artwork ? (
          <div className="mb-2.5 flex justify-center rounded-xl bg-[#101010] p-3">
            <img
              src={assetUrl(artwork.id)}
              alt={`attempt ${String(attempt.attempt_number)} artwork`}
              className="max-h-[260px] max-w-full"
            />
          </div>
        ) : null}

        {settled ? null : (
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
            className={cx(
              "cursor-pointer rounded-xl border-2 border-dashed p-[22px] text-center",
              dragging ? "border-lime bg-paper-2" : "border-paper-2 bg-transparent",
            )}
          >
            <ParagraphSmall className="mt-0 mb-0">
              {busy === "upload"
                ? "Storing the artwork…"
                : artwork
                  ? "Drop a replacement, or click to choose one."
                  : "Drop the artwork here, or click to choose a file."}
            </ParagraphSmall>
            {/* The reason, where the drop happened. It is also shown at the top
                of the panel, which on a phone is several screens above the
                control that caused it -- so a refused upload read as the
                message changing back and nothing else happening. */}
            {uploadError ? (
              <ParagraphXSmall className="mb-0 text-coral">{uploadError}</ParagraphXSmall>
            ) : null}
            <input
              ref={fileInput}
              type="file"
              accept="image/*,.svg"
              aria-label="Attach artwork to this attempt"
              className="hidden"
              onChange={(event) => {
                const file = event.currentTarget.files?.[0];
                if (file) onFile(file);
                event.currentTarget.value = "";
              }}
            />
          </div>
        )}

        {artwork && !settled ? (
          <div className="mt-2.5">
            <Button
              size="compact"
              variant="secondary"
              disabled={busy !== null}
              onClick={() => {
                void run("measure", () => measureAttempt(attempt.id));
              }}
            >
              {busy === "measure" ? "Measuring…" : "Measure this artwork"}
            </Button>
            <ParagraphXSmall className="mb-0 text-ink/50">
              Measurement fills only what nobody has answered, and never overwrites a person&rsquo;s
              answer. It is the start of a review, not a verdict.
            </ParagraphXSmall>
          </div>
        ) : null}

        {review && Object.keys(review.measurements).length > 0 ? (
          <ParagraphXSmall className="text-ink/70">
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
              <div key={group.id} className="mt-[18px]">
                <h3 className="mt-0 mb-0.5 text-[15px] font-bold text-ink">{group.label}</h3>
                <ParagraphXSmall className="mt-0 text-ink/50">{group.blurb}</ParagraphXSmall>

                {gates.map((gate) => {
                  const answered = review.gates.find((item) => item.id === gate.id);
                  const result = answered?.result ?? "not_tested";
                  // The brief answers some gates as fact. They are shown with
                  // their evidence and never offered as a choice.
                  if (review.derived_gates.includes(gate.id)) {
                    return (
                      <div key={gate.id} className="mt-2.5 border-t border-paper-2 pt-2.5">
                        <ParagraphSmall className="mt-0 mb-0.5">{gate.question}</ParagraphSmall>
                        <ParagraphXSmall className="mt-0 mb-0">
                          <strong className={result === "pass" ? "text-ink" : "text-coral"}>
                            {result === "pass" ? "Pass" : "Fail"}
                          </strong>{" "}
                          — from the brief: {answered?.evidence ?? "not recorded"}
                        </ParagraphXSmall>
                      </div>
                    );
                  }
                  return (
                    <div key={gate.id} className="mt-2.5 border-t border-paper-2 pt-2.5">
                      <ParagraphSmall className="mt-0 mb-1.5">{gate.question}</ParagraphSmall>
                      <div className="flex flex-wrap gap-1.5">
                        {RESULTS.map((option) => (
                          <button
                            key={option.id}
                            type="button"
                            disabled={settled || busy !== null}
                            aria-pressed={result === option.id}
                            aria-label={`${gate.label}: ${option.label}`}
                            onClick={() => {
                              answerGate(gate.id, option.id);
                            }}
                            className={chip(result === option.id, option.id === "fail")}
                          >
                            {option.label}
                          </button>
                        ))}
                      </div>
                      {answered?.evidence ? (
                        <ParagraphXSmall className="mb-0 text-ink/50">
                          {answered.evidence}
                        </ParagraphXSmall>
                      ) : null}
                    </div>
                  );
                })}

                {categories.map((category) => {
                  const rating = ratingOf(category.id);
                  return (
                    <div key={category.id} className="mt-2.5 border-t border-paper-2 pt-2.5">
                      <ParagraphSmall className="mt-0 mb-0.5">
                        <strong>{category.label}</strong> — {category.prompt}
                      </ParagraphSmall>
                      <ParagraphXSmall className="mt-0 text-ink/50">
                        {category.maximum} points. Release needs at least {category.ratingFloor}
                        /5.
                      </ParagraphXSmall>
                      <div className="flex flex-wrap gap-1.5">
                        {[0, 1, 2, 3, 4, 5].map((value) => (
                          <button
                            key={value}
                            type="button"
                            disabled={settled || busy !== null}
                            aria-pressed={rating === value}
                            aria-label={`${category.label}: ${String(value)} — ${
                              rubric.ratingMeanings[value] ?? ""
                            }`}
                            title={rubric.ratingMeanings[value] ?? ""}
                            onClick={() => {
                              rateCategory(category.id, value);
                            }}
                            className={chip(rating === value, value < category.ratingFloor)}
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
      {settled ? null : (
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
            <div className="mb-2.5">
              <Button
                size="compact"
                variant="ghost"
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
              <ParagraphXSmall className="mb-0 text-ink/50">
                For a row that should not have been made — the wrong concept, a prompt that belongs
                to another idea. Put the reason in the box above; the row is kept.
              </ParagraphXSmall>
            </div>
          ) : null}

          {attempt.state === "generated" ? (
            <Button
              size="compact"
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
              <div className="flex flex-wrap gap-1.5">
                <Button
                  size="compact"
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
                  size="compact"
                  variant="secondary"
                  disabled={busy !== null}
                  onClick={() => {
                    void run("decide", () => decide(attempt.id, "rejected", actor, note));
                  }}
                >
                  Reject
                </Button>
                <Button
                  size="compact"
                  variant="ghost"
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
                <ParagraphXSmall className="mb-0 text-ink/50">
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
          <ParagraphXSmall className="mt-0 text-ink/50">
            Print needs all three. Artwork made in a paid interface comes back as pixels, and pixels
            have no physical size — so the print width is a decision recorded here, frozen with the
            approval.
          </ParagraphXSmall>
          {Object.keys(garments).length === 0 ? (
            <Notification kind="warning">
              No garment files are present, so there are no zones to choose. Add a garment SVG to
              assets/garments.
            </Notification>
          ) : null}
          <div className="grid grid-cols-[repeat(auto-fit,minmax(180px,1fr))] gap-2.5">
            <FormControl label="Garment">
              <Select
                options={Object.keys(garments).map((key) => ({ value: key, label: key }))}
                value={garment}
                placeholder="Choose a garment"
                onChange={(value) => {
                  setGarment(value);
                  setZone("");
                }}
              />
            </FormControl>
            <FormControl label="Print zone">
              <Select
                options={(garments[garment] ?? []).map((item) => ({
                  value: item.key,
                  label: `${item.key} — ${String(item.width_mm)}×${String(item.height_mm)}mm`,
                }))}
                value={zone}
                placeholder={garment ? "Choose a zone" : "Choose a garment first"}
                disabled={garment === ""}
                onChange={(value) => {
                  setZone(value);
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
            size="compact"
            disabled={
              busy !== null ||
              garment === "" ||
              zone === "" ||
              !printWidth ||
              Number(printWidth) <= 0
            }
            onClick={() => {
              void run("approve", () =>
                approveDesignWithSpec(attempt.id, actor || "owner", {
                  garment_key: garment,
                  zone_key: zone,
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
          <div className="mt-2.5 flex justify-center rounded-xl bg-paper-2 p-3">
            <img
              src={printedVersionUrl(version.id)}
              alt={`version ${String(version.version)} printed on the garment`}
              className="max-h-[420px] max-w-full"
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
  return (
    <div className="mb-2.5 rounded-xl bg-paper-2 px-3.5 py-3">
      <span className="text-[22px] font-bold text-ink">{evaluation.percentage.toFixed(0)}/100</span>{" "}
      <span className="text-[13px] text-ink/70">{evaluation.bandLabel}</span>
      {evaluation.blockers.length > 0 ? (
        <ul className="mt-2 mb-0 pl-[18px] text-[13px] leading-[1.5] text-ink/70">
          {evaluation.blockers.map((blocker) => (
            <li key={blocker}>{blocker}</li>
          ))}
        </ul>
      ) : (
        <ParagraphXSmall className="mb-0">
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

/** A pill-shaped answer chip. `accent` marks the coral (fail / below-floor)
 * reading when active; the default active reading is ink. */
function chip(active: boolean, accent = false): string {
  return cx(
    "press appearance-none rounded-full border-none px-3 py-1.5 font-sans text-[12px] font-bold tracking-[0.03em] cursor-pointer disabled:cursor-default disabled:opacity-60",
    active ? (accent ? "bg-coral text-paper" : "bg-ink text-paper") : "bg-paper-2 text-ink/70",
  );
}

/**
 * The design backlog, as a bench.
 *
 * Three panels, matching the pipeline's shape. The review queue first, because
 * attempts awaiting a decision are the only thing here that blocks on a person.
 * Then the queue's answer to "what next" — the one accent moment on the page,
 * because it is the one thing the page exists to say. Then the backlog itself:
 * 260 numbered concepts where the default state is unmarked and a chip only
 * appears when a state is worth marking.
 *
 * Deciding follows the compose bench's rule: a decision needs a name against
 * it, checked here as well as by the server, because an approval nobody signed
 * is not an approval.
 */

import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../api/client";
import {
  assetUrl,
  decideAttempt,
  fetchConcept,
  fetchConcepts,
  fetchNextConcept,
  fetchReviewQueue,
  type ConceptDetailView,
  type ConceptStatus,
  type ConceptView,
  type DesignAttemptView,
  type DesignDecisionKind,
} from "../api/concepts";
import { AttemptPanel } from "./AttemptPanel";
import { BriefPanel } from "./BriefPanel";
import { ComposeBench } from "./ComposeBench";
import { DesignBench } from "./DesignBench";
import { Disclosure, PageTitle, SectionTitle, StatusChip } from "./chrome";
import { Button, Card, cx, FormControl, Input, Notification, ParagraphSmall, ParagraphXSmall } from "./ui";

function describe(cause: unknown): string {
  if (cause instanceof ApiError) return cause.message;
  return cause instanceof Error ? cause.message : String(cause);
}

const STATUS_FILTERS: { id: string; label: string }[] = [
  { id: "", label: "All" },
  { id: "backlog", label: "Backlog" },
  { id: "ready", label: "Ready" },
  { id: "exploring", label: "Exploring" },
  { id: "approved", label: "Approved" },
  { id: "held", label: "Held" },
  { id: "retired", label: "Retired" },
];

const metaLineClass = "text-[12px] font-semibold tracking-wide uppercase text-ink/50";

function number3(value: number): string {
  return `#${String(value).padStart(3, "0")}`;
}

export interface DesignsBenchProps {
  /** A concept, and optionally an attempt, that Work asked us to open. Work is
   * a way in rather than a second place to do the job, so it hands over rather
   * than duplicating the screen. */
  focus?: { conceptId: string; attemptId: string | null } | null;
  onFocusConsumed?: () => void;
}

export function DesignsBench({
  focus,
  onFocusConsumed,
}: DesignsBenchProps = {}): React.JSX.Element {
  const [queue, setQueue] = useState<DesignAttemptView[]>([]);
  const [nextUp, setNextUp] = useState<ConceptView | null>(null);
  const [concepts, setConcepts] = useState<ConceptView[]>([]);
  const [filter, setFilter] = useState("");
  const [selected, setSelected] = useState<ConceptDetailView | null>(null);
  // Which attempt is open. The attempt panel is the whole flow -- brief,
  // artwork, measurement, scorecard, decision -- so it opens in place rather
  // than becoming an eleventh top-level destination.
  const [openAttemptId, setOpenAttemptId] = useState<string | null>(null);
  const [decider, setDecider] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [queued, next, listed] = await Promise.all([
        fetchReviewQueue(),
        fetchNextConcept(),
        fetchConcepts(filter === "" ? undefined : (filter as ConceptStatus)),
      ]);
      setQueue(queued);
      setNextUp(next);
      setConcepts(listed);
    } catch (cause) {
      setError(describe(cause));
    }
  }, [filter]);

  useEffect(() => {
    const timer = setTimeout(() => {
      void refresh();
    }, 0);
    return () => {
      clearTimeout(timer);
    };
  }, [refresh]);

  const open = useCallback(async (conceptId: string) => {
    try {
      setSelected(await fetchConcept(conceptId));
    } catch (cause) {
      setError(describe(cause));
    }
  }, []);

  const onDecide = useCallback(
    async (attempt: DesignAttemptView, decision: DesignDecisionKind) => {
      if (!decider.trim()) {
        setError("A decision needs a name against it.");
        return;
      }
      setBusy(true);
      setError(null);
      try {
        await decideAttempt(attempt.id, decision, decider.trim());
        await refresh();
        if (selected && selected.id === attempt.concept_id) await open(attempt.concept_id);
      } catch (cause) {
        setError(describe(cause));
      } finally {
        setBusy(false);
      }
    },
    [decider, refresh, selected, open],
  );

  /** Take the reviewer to the attempt, which is the only place it can be
   * judged. The queue answers "what is waiting"; the attempt answers "why". */
  const openAttempt = useCallback(
    async (attempt: DesignAttemptView) => {
      await open(attempt.concept_id);
      setOpenAttemptId(attempt.id);
    },
    [open],
  );

  // Consumed once. Navigating away and back should not silently re-open what
  // Work pointed at three screens ago.
  useEffect(() => {
    if (!focus) return;
    const timer = setTimeout(() => {
      void open(focus.conceptId).then(() => {
        setOpenAttemptId(focus.attemptId);
        onFocusConsumed?.();
      });
    }, 0);
    return () => {
      clearTimeout(timer);
    };
  }, [focus, open, onFocusConsumed]);

  const preview = (attempt: DesignAttemptView) => {
    const artwork = attempt.assets.find((asset) => asset.kind === "artwork") ?? attempt.assets[0];
    if (!artwork) return null;
    return (
      <div className="mb-2.5 flex justify-center rounded-xl bg-[#101010] p-3">
        <img
          src={assetUrl(artwork.id)}
          alt={`attempt ${String(attempt.attempt_number)}`}
          className="max-h-[200px] max-w-full"
        />
      </div>
    );
  };

  return (
    <>
      <PageTitle meta={`${String(concepts.length)} concepts`}>Designs</PageTitle>
      <ParagraphSmall>
        The concept library as a working queue. The numbers are permanent, the statuses are real,
        and &ldquo;next&rdquo; is a query rather than a memory.
      </ParagraphSmall>

      {error ? <Notification kind="negative">{error}</Notification> : null}

      <div className="mb-6 max-w-[280px]">
        <FormControl label="Deciding as">
          <Input
            value={decider}
            placeholder="your name"
            onChange={(event) => {
              setDecider(event.currentTarget.value);
            }}
          />
        </FormControl>
      </div>

      <SectionTitle count={queue.length}>Review</SectionTitle>
      {queue.length === 0 ? (
        <ParagraphSmall>Nothing awaits a decision.</ParagraphSmall>
      ) : (
        <div className="mb-7 grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-3">
          {queue.map((attempt) => (
            <Card key={attempt.id}>
              {preview(attempt)}
              <span className={metaLineClass}>
                attempt {attempt.attempt_number} · {attempt.method.replace(/_/g, " ")}
              </span>
              {/* No Approve here. Approval needs the scorecard answered and
                  the queue has nowhere to answer it, so the queue's job is
                  to get you to the attempt. Rejecting and asking for a
                  variation need no rubric and stay. */}
              <div className="mt-2.5 flex gap-1.5">
                <Button
                  size="compact"
                  disabled={busy}
                  onClick={() => {
                    void openAttempt(attempt);
                  }}
                >
                  Judge it
                </Button>
                <Button
                  size="compact"
                  variant="secondary"
                  disabled={busy}
                  onClick={() => {
                    void onDecide(attempt, "rejected");
                  }}
                >
                  Reject
                </Button>
                <Button
                  size="compact"
                  variant="ghost"
                  disabled={busy}
                  onClick={() => {
                    void onDecide(attempt, "variation_requested");
                  }}
                >
                  Variation
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {nextUp ? (
        // The page's one accent moment: ink surface, lime eyebrow, display
        // type. What to do next is the thing this bench exists to answer.
        // Ink on paper in both themes: this is a brand statement, not a
        // theme surface, so it stays hard-coded to bg-ink/text-paper rather
        // than following dark mode's inverse -- a hairline keeps the ink
        // card separate from an ink page instead.
        <section className="mt-6 mb-8 rounded-[20px] border border-paper/[0.14] bg-ink px-6 py-6 text-paper">
          <span className="mb-2.5 block text-[11px] font-bold tracking-[0.12em] text-lime uppercase">
            Next up
          </span>
          <h2 className="display mb-2.5 text-[clamp(26px,5vw,36px)] text-inherit">
            {number3(nextUp.external_number)} {nextUp.title}
          </h2>
          <p className="mb-3.5 max-w-[640px] text-[15px] leading-[1.55] opacity-75">
            {nextUp.concept_text}
          </p>
          <div className="flex flex-wrap gap-1.5">
            {nextUp.garments.map((garment) => (
              <span
                key={garment}
                className="rounded-lg bg-paper/[0.14] px-2 py-[3px] text-[11px] font-bold tracking-wide uppercase"
              >
                {garment}
              </span>
            ))}
          </div>
        </section>
      ) : null}

      <div className="flex flex-wrap items-center gap-3">
        <SectionTitle count={concepts.length}>Backlog</SectionTitle>
        <div className="flex flex-wrap gap-1">
          {STATUS_FILTERS.map((item) => (
            <button
              key={item.id}
              type="button"
              aria-pressed={filter === item.id}
              onClick={() => {
                setFilter(item.id);
                setSelected(null);
              }}
              className={cx(
                "press appearance-none rounded-full border-none px-3 py-1.5 font-sans text-[12px] font-bold tracking-wide uppercase",
                filter === item.id
                  ? "bg-ink text-paper"
                  : "bg-transparent text-ink/70 hover:bg-paper-2",
              )}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* One column on a phone: the two-column minimums add to ~600px and
          push the detail card off the right edge of the screen. */}
      <div className="grid grid-cols-1 items-start gap-4 md:grid-cols-[minmax(280px,1fr)_minmax(320px,1.2fr)]">
        <div className="max-h-[540px] overflow-y-auto rounded-2xl border border-paper-2 bg-paper">
          {concepts.map((concept) => (
            <button
              key={concept.id}
              type="button"
              onClick={() => {
                void open(concept.id);
              }}
              className={cx(
                "flex w-full items-center gap-2.5 border-0 border-b border-paper-2 px-3.5 py-2.5 text-left font-sans hover:bg-paper-2",
                selected?.id === concept.id
                  ? "bg-paper-2 shadow-[inset_3px_0_0_var(--color-ink)]"
                  : "bg-transparent",
              )}
            >
              <span className="text-[12px] font-semibold tabular-nums text-ink/50">
                {number3(concept.external_number)}
              </span>
              <span className="flex-1 truncate text-[13px] font-bold tracking-wide text-ink">
                {concept.title}
              </span>
              {/* Numbering is per-library, so #001 alone is ambiguous once a
                  second library exists. The tee library is the default and
                  stays unmarked; anything else says so. */}
              {concept.library !== "tshirt" ? (
                <StatusChip status={concept.library.replace(/_/g, " ")} />
              ) : null}
              {concept.attempt_count > 0 ? (
                <span className="text-[11px] text-ink/50">
                  {concept.attempt_count} {concept.attempt_count === 1 ? "attempt" : "attempts"}
                </span>
              ) : null}
              {/* The default state is unmarked. A chip marks an exception. */}
              {concept.status !== "backlog" ? <StatusChip status={concept.status} /> : null}
            </button>
          ))}
        </div>

        {/* Detail first on a phone: tapping a row should surface the lineage
            where the eye already is, not below a 540px list. */}
        <div className="order-first md:order-none">
          {selected ? (
            <Card>
              <span className={metaLineClass}>
                {number3(selected.external_number)} · {selected.round_label} · {selected.slug}
              </span>
              <h2 className="display mt-1.5 mb-2.5 text-[clamp(22px,4vw,30px)] text-ink">
                {selected.title}
              </h2>
              {/* The owner's words, verbatim. The pipeline never edits them. */}
              <ParagraphSmall>{selected.concept_text}</ParagraphSmall>

              <div className="mb-5 flex flex-wrap gap-1.5">
                <StatusChip status={selected.status} />
                {selected.retirement ? (
                  <StatusChip status={`${selected.retirement} retirement`} />
                ) : null}
                {selected.garments.map((garment) => (
                  <StatusChip key={garment} status={garment} />
                ))}
                {selected.approved_versions > 0 ? (
                  <StatusChip status={`v${String(selected.approved_versions)} approved`} />
                ) : null}
              </div>

              {selected.salvage ? (
                <div className="mb-5 rounded-xl bg-cream px-3.5 py-3 text-[13px] leading-normal text-ink">
                  Held, not retired: {selected.salvage}
                </div>
              ) : null}

              {/* The brief comes before the attempts, because the
                  constitution decides what a product is before any artwork
                  exists -- and because an attempt cannot be opened without
                  it, so a reader who scrolls past it hits a refusal. */}
              <BriefPanel
                conceptId={selected.id}
                conceptText={selected.concept_text}
                onChanged={async () => {
                  await refresh();
                  await open(selected.id);
                }}
              />

              {selected.attempts.length === 0 ? (
                <ParagraphSmall>Never attempted.</ParagraphSmall>
              ) : (
                selected.attempts.map((attempt) => (
                  <div key={attempt.id} className="mt-3 border-t border-paper-2 pt-3">
                    {preview(attempt)}
                    <div className="flex flex-wrap items-center gap-1.5">
                      <StatusChip status={attempt.state} />
                      <span className={metaLineClass}>
                        attempt {attempt.attempt_number} · {attempt.method.replace(/_/g, " ")}
                      </span>
                      {attempt.approved_version !== null ? (
                        <StatusChip status={`v${String(attempt.approved_version)} approved`} />
                      ) : null}
                    </div>
                    {attempt.decision ? (
                      <ParagraphXSmall className="mt-1.5">
                        {attempt.decision.decision.replace(/_/g, " ")} by {attempt.decision.actor}
                        {attempt.decision.reason ? ` — ${attempt.decision.reason}` : ""}
                        {attempt.decision.instruction ? ` — ${attempt.decision.instruction}` : ""}
                      </ParagraphXSmall>
                    ) : null}
                    <div className="mt-2">
                      <Button
                        size="compact"
                        variant={openAttemptId === attempt.id ? "primary" : "secondary"}
                        onClick={() => {
                          setOpenAttemptId(openAttemptId === attempt.id ? null : attempt.id);
                        }}
                      >
                        {openAttemptId === attempt.id ? "Close" : "Open this attempt"}
                      </Button>
                    </div>
                    {openAttemptId === attempt.id ? (
                      <div className="mt-3">
                        <AttemptPanel
                          concept={selected}
                          attempt={attempt}
                          actor={decider}
                          onChanged={async () => {
                            await refresh();
                            await open(selected.id);
                          }}
                        />
                      </div>
                    ) : null}
                  </div>
                ))
              )}
            </Card>
          ) : (
            <ParagraphSmall>Select a concept to see its lineage.</ParagraphSmall>
          )}
        </div>
      </div>

      {/* Phase 5. Compose and Score were top-level destinations, which made the
          design journey three screens that each knew part of it. They are the
          same capabilities, reached from the one screen that owns the journey.
          Closed by default and mounted only when opened, so a backlog does not
          pay for three benches' worth of fetching. */}
      <Disclosure
        label="Compose artwork"
        blurb="The deterministic composer: a garment, some words, a seed. Same seed, same bytes."
      >
        {() => <ComposeBench />}
      </Disclosure>

      <Disclosure
        label="Measure a loose file"
        blurb="For something that is not a concept yet. An attempt measures its own artwork."
      >
        {() => <DesignBench />}
      </Disclosure>
    </>
  );
}

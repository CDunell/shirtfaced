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
import { useStyletron } from "baseui";
import { Button, KIND as BUTTON_KIND, SIZE } from "baseui/button";
import { Card, StyledBody } from "baseui/card";
import { FormControl } from "baseui/form-control";
import { Input } from "baseui/input";
import { Notification, KIND as NOTIFICATION_KIND } from "baseui/notification";
import { ParagraphSmall, ParagraphXSmall } from "baseui/typography";

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
import { PageTitle, SectionTitle, StatusChip } from "./chrome";
import { CREAM, INK, LIME, PAPER } from "../tokens";

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
  const [css, theme] = useStyletron();
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
          alt={`attempt ${String(attempt.attempt_number)}`}
          className={css({ maxWidth: "100%", maxHeight: "200px" })}
        />
      </div>
    );
  };

  const metaLine = css({
    fontSize: "12px",
    fontWeight: 600,
    letterSpacing: "0.04em",
    textTransform: "uppercase",
    color: theme.colors.contentTertiary,
  });

  return (
    <>
      <PageTitle meta={`${String(concepts.length)} concepts`}>Designs</PageTitle>
      <ParagraphSmall color={theme.colors.contentSecondary} marginTop={0}>
        The concept library as a working queue. The numbers are permanent, the statuses are real,
        and &ldquo;next&rdquo; is a query rather than a memory.
      </ParagraphSmall>

      {error ? (
        <Notification
          kind={NOTIFICATION_KIND.negative}
          overrides={{ Body: { style: { width: "auto" } } }}
        >
          {error}
        </Notification>
      ) : null}

      <div className={css({ maxWidth: "280px", marginBottom: theme.sizing.scale600 })}>
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
        <ParagraphSmall color={theme.colors.contentSecondary} marginTop={0}>
          Nothing awaits a decision.
        </ParagraphSmall>
      ) : (
        <div
          className={css({
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
            gap: "12px",
            marginBottom: theme.sizing.scale700,
          })}
        >
          {queue.map((attempt) => (
            <Card key={attempt.id}>
              <StyledBody>
                {preview(attempt)}
                <span className={metaLine}>
                  attempt {attempt.attempt_number} · {attempt.method.replace(/_/g, " ")}
                </span>
                {/* No Approve here. Approval needs the scorecard answered and
                    the queue has nowhere to answer it, so the queue's job is
                    to get you to the attempt. Rejecting and asking for a
                    variation need no rubric and stay. */}
                <div className={css({ display: "flex", gap: "6px", marginTop: "10px" })}>
                  <Button
                    size={SIZE.mini}
                    disabled={busy}
                    onClick={() => {
                      void openAttempt(attempt);
                    }}
                  >
                    Judge it
                  </Button>
                  <Button
                    size={SIZE.mini}
                    kind={BUTTON_KIND.secondary}
                    disabled={busy}
                    onClick={() => {
                      void onDecide(attempt, "rejected");
                    }}
                  >
                    Reject
                  </Button>
                  <Button
                    size={SIZE.mini}
                    kind={BUTTON_KIND.tertiary}
                    disabled={busy}
                    onClick={() => {
                      void onDecide(attempt, "variation_requested");
                    }}
                  >
                    Variation
                  </Button>
                </div>
              </StyledBody>
            </Card>
          ))}
        </div>
      )}

      {nextUp ? (
        // The page's one accent moment: ink surface, lime eyebrow, display
        // type. What to do next is the thing this bench exists to answer.
        <section
          className={css({
            // Ink on paper in both themes: this is a brand statement, not a
            // theme surface. In dark mode the theme's "inverse" turns light
            // grey and the lime eyebrow dies on it; a hairline keeps the ink
            // card separate from an ink page instead.
            backgroundColor: INK,
            color: PAPER,
            border: `1px solid color-mix(in srgb, ${PAPER} 14%, transparent)`,
            borderRadius: "20px",
            paddingTop: "24px",
            paddingBottom: "24px",
            paddingLeft: "24px",
            paddingRight: "24px",
            marginTop: theme.sizing.scale600,
            marginBottom: theme.sizing.scale800,
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
              marginBottom: "10px",
            })}
          >
            Next up
          </span>
          <h2
            className={`display ${css({
              fontSize: "clamp(26px, 5vw, 36px)",
              margin: "0 0 10px",
              color: "inherit",
            })}`}
          >
            {number3(nextUp.external_number)} {nextUp.title}
          </h2>
          <p
            className={css({
              margin: "0 0 14px",
              fontSize: "15px",
              lineHeight: 1.55,
              opacity: 0.75,
              maxWidth: "640px",
            })}
          >
            {nextUp.concept_text}
          </p>
          <div className={css({ display: "flex", gap: "6px", flexWrap: "wrap" })}>
            {nextUp.garments.map((garment) => (
              <span
                key={garment}
                className={css({
                  fontSize: "11px",
                  fontWeight: 700,
                  letterSpacing: "0.06em",
                  textTransform: "uppercase",
                  borderRadius: "8px",
                  paddingTop: "3px",
                  paddingBottom: "3px",
                  paddingLeft: "8px",
                  paddingRight: "8px",
                  backgroundColor: "rgba(242, 240, 237, 0.14)",
                  color: "inherit",
                })}
              >
                {garment}
              </span>
            ))}
          </div>
        </section>
      ) : null}

      <div
        className={css({
          display: "flex",
          alignItems: "center",
          gap: "12px",
          flexWrap: "wrap",
        })}
      >
        <SectionTitle count={concepts.length}>Backlog</SectionTitle>
        <div className={css({ display: "flex", gap: "4px", flexWrap: "wrap" })}>
          {STATUS_FILTERS.map((item) => (
            <button
              key={item.id}
              type="button"
              aria-pressed={filter === item.id}
              onClick={() => {
                setFilter(item.id);
                setSelected(null);
              }}
              className={`press ${css({
                appearance: "none",
                border: "none",
                cursor: "pointer",
                fontFamily: "inherit",
                fontSize: "12px",
                fontWeight: 700,
                letterSpacing: "0.04em",
                textTransform: "uppercase",
                borderRadius: "999px",
                paddingTop: "6px",
                paddingBottom: "6px",
                paddingLeft: "12px",
                paddingRight: "12px",
                backgroundColor: filter === item.id ? theme.colors.contentPrimary : "transparent",
                color:
                  filter === item.id
                    ? theme.colors.backgroundPrimary
                    : theme.colors.contentSecondary,
                ":hover":
                  filter === item.id ? {} : { backgroundColor: theme.colors.backgroundSecondary },
              })}`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <div
        className={css({
          display: "grid",
          gridTemplateColumns: "minmax(280px, 1fr) minmax(320px, 1.2fr)",
          gap: "16px",
          alignItems: "start",
          // One column on a phone: the two-column minimums add to ~600px and
          // push the detail card off the right edge of the screen.
          "@media screen and (max-width: 760px)": { gridTemplateColumns: "1fr" },
        })}
      >
        <div
          className={css({
            maxHeight: "540px",
            overflowY: "auto",
            backgroundColor: theme.colors.backgroundPrimary,
            border: `1px solid ${theme.colors.backgroundSecondary}`,
            borderRadius: "16px",
          })}
        >
          {concepts.map((concept) => (
            <button
              key={concept.id}
              type="button"
              onClick={() => {
                void open(concept.id);
              }}
              className={css({
                display: "flex",
                width: "100%",
                alignItems: "center",
                gap: "10px",
                appearance: "none",
                border: "none",
                borderBottom: `1px solid ${theme.colors.backgroundSecondary}`,
                cursor: "pointer",
                fontFamily: "inherit",
                textAlign: "left",
                paddingTop: "10px",
                paddingBottom: "10px",
                paddingLeft: "14px",
                paddingRight: "14px",
                backgroundColor:
                  selected?.id === concept.id ? theme.colors.backgroundSecondary : "transparent",
                boxShadow:
                  selected?.id === concept.id
                    ? `inset 3px 0 0 ${theme.colors.contentPrimary}`
                    : "none",
                ":hover": { backgroundColor: theme.colors.backgroundSecondary },
              })}
            >
              <span
                className={css({
                  fontVariantNumeric: "tabular-nums",
                  color: theme.colors.contentTertiary,
                  fontSize: "12px",
                  fontWeight: 600,
                })}
              >
                {number3(concept.external_number)}
              </span>
              <span
                className={css({
                  flex: "1 1 auto",
                  fontSize: "13px",
                  fontWeight: 700,
                  letterSpacing: "0.01em",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                  color: theme.colors.contentPrimary,
                })}
              >
                {concept.title}
              </span>
              {/* Numbering is per-library, so #001 alone is ambiguous once a
                  second library exists. The tee library is the default and
                  stays unmarked; anything else says so. */}
              {concept.library !== "tshirt" ? (
                <StatusChip status={concept.library.replace(/_/g, " ")} />
              ) : null}
              {concept.attempt_count > 0 ? (
                <span className={css({ fontSize: "11px", color: theme.colors.contentTertiary })}>
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
        <div className={css({ "@media screen and (max-width: 760px)": { order: -1 } })}>
          {selected ? (
            <Card>
              <StyledBody>
                <span className={metaLine}>
                  {number3(selected.external_number)} · {selected.round_label} · {selected.slug}
                </span>
                <h2
                  className={`display ${css({
                    fontSize: "clamp(22px, 4vw, 30px)",
                    margin: "6px 0 10px",
                    color: theme.colors.contentPrimary,
                  })}`}
                >
                  {selected.title}
                </h2>
                {/* The owner's words, verbatim. The pipeline never edits them. */}
                <ParagraphSmall marginTop={0}>{selected.concept_text}</ParagraphSmall>

                <div
                  className={css({
                    display: "flex",
                    gap: "6px",
                    flexWrap: "wrap",
                    marginBottom: theme.sizing.scale500,
                  })}
                >
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
                  <div
                    className={css({
                      backgroundColor: CREAM,
                      color: "#0d0d0d",
                      borderRadius: "12px",
                      paddingTop: "12px",
                      paddingBottom: "12px",
                      paddingLeft: "14px",
                      paddingRight: "14px",
                      fontSize: "13px",
                      lineHeight: 1.5,
                      marginBottom: theme.sizing.scale500,
                    })}
                  >
                    Held, not retired: {selected.salvage}
                  </div>
                ) : null}

                {selected.attempts.length === 0 ? (
                  <ParagraphSmall color={theme.colors.contentSecondary}>
                    Never attempted.
                  </ParagraphSmall>
                ) : (
                  selected.attempts.map((attempt) => (
                    <div
                      key={attempt.id}
                      className={css({
                        borderTop: `1px solid ${theme.colors.backgroundSecondary}`,
                        paddingTop: "12px",
                        marginTop: "12px",
                      })}
                    >
                      {preview(attempt)}
                      <div
                        className={css({
                          display: "flex",
                          gap: "6px",
                          flexWrap: "wrap",
                          alignItems: "center",
                        })}
                      >
                        <StatusChip status={attempt.state} />
                        <span className={metaLine}>
                          attempt {attempt.attempt_number} · {attempt.method.replace(/_/g, " ")}
                        </span>
                        {attempt.approved_version !== null ? (
                          <StatusChip status={`v${String(attempt.approved_version)} approved`} />
                        ) : null}
                      </div>
                      {attempt.decision ? (
                        <ParagraphXSmall marginTop="6px" color={theme.colors.contentSecondary}>
                          {attempt.decision.decision.replace(/_/g, " ")} by {attempt.decision.actor}
                          {attempt.decision.reason ? ` — ${attempt.decision.reason}` : ""}
                          {attempt.decision.instruction ? ` — ${attempt.decision.instruction}` : ""}
                        </ParagraphXSmall>
                      ) : null}
                      <div className={css({ marginTop: "8px" })}>
                        <Button
                          size={SIZE.mini}
                          kind={
                            openAttemptId === attempt.id
                              ? BUTTON_KIND.primary
                              : BUTTON_KIND.secondary
                          }
                          onClick={() => {
                            setOpenAttemptId(openAttemptId === attempt.id ? null : attempt.id);
                          }}
                        >
                          {openAttemptId === attempt.id ? "Close" : "Open this attempt"}
                        </Button>
                      </div>
                      {openAttemptId === attempt.id ? (
                        <div className={css({ marginTop: "12px" })}>
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
              </StyledBody>
            </Card>
          ) : (
            <ParagraphSmall color={theme.colors.contentSecondary} marginTop={0}>
              Select a concept to see its lineage.
            </ParagraphSmall>
          )}
        </div>
      </div>
    </>
  );
}

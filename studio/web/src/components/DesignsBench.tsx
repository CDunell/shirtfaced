/**
 * The design backlog, as a bench.
 *
 * Three panels, matching the pipeline's shape. The review queue first, because
 * attempts awaiting a decision are the only thing here that blocks on a person.
 * Then the queue's answer to "what next". Then the backlog itself: 260 numbered
 * concepts with their real states, where "worked on" means attempts exist in
 * the database rather than someone remembering a conversation.
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
import { Select, type Value } from "baseui/select";
import { Tag, KIND as TAG_KIND } from "baseui/tag";
import { HeadingSmall, LabelSmall, ParagraphSmall, ParagraphXSmall } from "baseui/typography";

import { ApiError } from "../api/client";
import {
  approveDesign,
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

function statusTagKind(status: string): (typeof TAG_KIND)[keyof typeof TAG_KIND] {
  switch (status) {
    case "approved":
      return TAG_KIND.positive;
    case "rejected":
    case "retired":
      return TAG_KIND.negative;
    case "exploring":
    case "awaiting_decision":
      return TAG_KIND.warning;
    default:
      return TAG_KIND.neutral;
  }
}

export function DesignsBench(): React.JSX.Element {
  const [css, theme] = useStyletron();
  const [queue, setQueue] = useState<DesignAttemptView[]>([]);
  const [nextUp, setNextUp] = useState<ConceptView | null>(null);
  const [concepts, setConcepts] = useState<ConceptView[]>([]);
  const [filter, setFilter] = useState<Value>([{ id: "", label: "All" }]);
  const [selected, setSelected] = useState<ConceptDetailView | null>(null);
  const [decider, setDecider] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const status = String(filter[0]?.id ?? "");
      const [queued, next, listed] = await Promise.all([
        fetchReviewQueue(),
        fetchNextConcept(),
        fetchConcepts(status === "" ? undefined : (status as ConceptStatus)),
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

  const onApproveDesign = useCallback(
    async (attempt: DesignAttemptView) => {
      if (!decider.trim()) {
        setError("A version needs a name against it.");
        return;
      }
      setBusy(true);
      setError(null);
      try {
        await approveDesign(attempt.id, decider.trim());
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

  const preview = (attempt: DesignAttemptView) => {
    const artwork = attempt.assets.find((asset) => asset.kind === "artwork") ?? attempt.assets[0];
    if (!artwork) return null;
    return (
      <div
        className={css({
          background: "#101010",
          borderRadius: "6px",
          padding: "10px",
          marginBottom: "8px",
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

  return (
    <>
      <HeadingSmall marginTop={0} marginBottom={theme.sizing.scale300}>
        Designs
      </HeadingSmall>
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

      <HeadingSmall marginBottom={theme.sizing.scale300}>Review</HeadingSmall>
      {queue.length === 0 ? (
        <ParagraphSmall color={theme.colors.contentSecondary}>
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
                <LabelSmall>
                  attempt {attempt.attempt_number} · {attempt.method.replace(/_/g, " ")}
                </LabelSmall>
                <div className={css({ display: "flex", gap: "6px", marginTop: "8px" })}>
                  <Button
                    size={SIZE.mini}
                    disabled={busy}
                    onClick={() => {
                      void onDecide(attempt, "approved");
                    }}
                  >
                    Approve
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
        <Card
          overrides={{
            Root: {
              style: {
                marginTop: theme.sizing.scale600,
                marginBottom: theme.sizing.scale700,
              },
            },
          }}
        >
          <StyledBody>
            <LabelSmall color={theme.colors.contentSecondary}>Next up</LabelSmall>
            <HeadingSmall marginTop="4px" marginBottom="4px">
              #{String(nextUp.external_number).padStart(3, "0")} {nextUp.title}
            </HeadingSmall>
            <ParagraphSmall marginTop={0}>{nextUp.concept_text}</ParagraphSmall>
            <div className={css({ display: "flex", gap: "4px", flexWrap: "wrap" })}>
              <Tag closeable={false} kind={statusTagKind(nextUp.status)}>
                {nextUp.status}
              </Tag>
              {nextUp.garments.map((garment) => (
                <Tag key={garment} closeable={false} kind={TAG_KIND.neutral}>
                  {garment}
                </Tag>
              ))}
            </div>
          </StyledBody>
        </Card>
      ) : null}

      <div
        className={css({
          display: "flex",
          alignItems: "center",
          gap: "12px",
          marginBottom: theme.sizing.scale300,
        })}
      >
        <HeadingSmall marginTop={0} marginBottom={0}>
          Backlog
        </HeadingSmall>
        <div className={css({ width: "180px" })}>
          <Select
            clearable={false}
            searchable={false}
            size="compact"
            options={STATUS_FILTERS}
            value={filter}
            onChange={({ value }) => {
              setFilter(value);
              setSelected(null);
            }}
          />
        </div>
        <ParagraphXSmall color={theme.colors.contentSecondary}>
          {concepts.length} concepts
        </ParagraphXSmall>
      </div>

      <div
        className={css({
          display: "grid",
          gridTemplateColumns: "minmax(280px, 1fr) minmax(320px, 1.2fr)",
          gap: "16px",
          alignItems: "start",
        })}
      >
        <div
          className={css({
            maxHeight: "540px",
            overflowY: "auto",
            border: `1px solid ${theme.colors.borderOpaque}`,
            borderRadius: "8px",
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
                gap: "8px",
                appearance: "none",
                border: "none",
                borderBottom: `1px solid ${theme.colors.borderOpaque}`,
                cursor: "pointer",
                fontFamily: "inherit",
                textAlign: "left",
                paddingTop: "8px",
                paddingBottom: "8px",
                paddingLeft: "12px",
                paddingRight: "12px",
                backgroundColor:
                  selected?.id === concept.id ? theme.colors.backgroundSecondary : "transparent",
                ":hover": { backgroundColor: theme.colors.backgroundSecondary },
              })}
            >
              <span
                className={css({
                  fontVariantNumeric: "tabular-nums",
                  color: theme.colors.contentTertiary,
                  fontSize: "12px",
                })}
              >
                #{String(concept.external_number).padStart(3, "0")}
              </span>
              <span
                className={css({
                  flex: "1 1 auto",
                  fontSize: "13px",
                  fontWeight: 600,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                })}
              >
                {concept.title}
              </span>
              {concept.attempt_count > 0 ? (
                <span className={css({ fontSize: "11px", color: theme.colors.contentTertiary })}>
                  {concept.attempt_count} {concept.attempt_count === 1 ? "attempt" : "attempts"}
                </span>
              ) : null}
              <Tag closeable={false} kind={statusTagKind(concept.status)}>
                {concept.status}
              </Tag>
            </button>
          ))}
        </div>

        {selected ? (
          <Card>
            <StyledBody>
              <LabelSmall color={theme.colors.contentSecondary}>
                #{String(selected.external_number).padStart(3, "0")} · {selected.round_label} ·{" "}
                {selected.slug}
              </LabelSmall>
              <HeadingSmall marginTop="4px" marginBottom="4px">
                {selected.title}
              </HeadingSmall>
              {/* The owner's words, verbatim. The pipeline never edits them. */}
              <ParagraphSmall marginTop={0}>{selected.concept_text}</ParagraphSmall>

              <div
                className={css({
                  display: "flex",
                  gap: "4px",
                  flexWrap: "wrap",
                  marginBottom: theme.sizing.scale300,
                })}
              >
                <Tag closeable={false} kind={statusTagKind(selected.status)}>
                  {selected.status}
                </Tag>
                {selected.retirement ? (
                  <Tag closeable={false} kind={TAG_KIND.negative}>
                    {selected.retirement} retirement
                  </Tag>
                ) : null}
                {selected.garments.map((garment) => (
                  <Tag key={garment} closeable={false} kind={TAG_KIND.neutral}>
                    {garment}
                  </Tag>
                ))}
                {selected.approved_versions > 0 ? (
                  <Tag closeable={false} kind={TAG_KIND.positive}>
                    v{selected.approved_versions}
                  </Tag>
                ) : null}
              </div>

              {selected.salvage ? (
                <Notification kind={NOTIFICATION_KIND.warning}>
                  Held, not retired: {selected.salvage}
                </Notification>
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
                      borderTop: `1px solid ${theme.colors.borderOpaque}`,
                      paddingTop: "8px",
                      marginTop: "8px",
                    })}
                  >
                    {preview(attempt)}
                    <div className={css({ display: "flex", gap: "4px", flexWrap: "wrap" })}>
                      <Tag closeable={false} kind={statusTagKind(attempt.state)}>
                        {attempt.state.replace(/_/g, " ")}
                      </Tag>
                      <Tag closeable={false} kind={TAG_KIND.neutral}>
                        attempt {attempt.attempt_number}
                      </Tag>
                      <Tag closeable={false} kind={TAG_KIND.neutral}>
                        {attempt.method.replace(/_/g, " ")}
                      </Tag>
                      {attempt.approved_version !== null ? (
                        <Tag closeable={false} kind={TAG_KIND.positive}>
                          v{attempt.approved_version}
                        </Tag>
                      ) : null}
                    </div>
                    {attempt.decision ? (
                      <ParagraphXSmall marginTop="4px" color={theme.colors.contentSecondary}>
                        {attempt.decision.decision.replace(/_/g, " ")} by {attempt.decision.actor}
                        {attempt.decision.reason ? ` — ${attempt.decision.reason}` : ""}
                        {attempt.decision.instruction ? ` — ${attempt.decision.instruction}` : ""}
                      </ParagraphXSmall>
                    ) : null}
                    {attempt.state === "approved" && attempt.approved_version === null ? (
                      <Button
                        size={SIZE.mini}
                        kind={BUTTON_KIND.secondary}
                        disabled={busy}
                        onClick={() => {
                          void onApproveDesign(attempt);
                        }}
                      >
                        Record approved design v{selected.approved_versions + 1}
                      </Button>
                    ) : null}
                  </div>
                ))
              )}
            </StyledBody>
          </Card>
        ) : (
          <ParagraphSmall color={theme.colors.contentSecondary}>
            Select a concept to see its lineage.
          </ParagraphSmall>
        )}
      </div>
    </>
  );
}

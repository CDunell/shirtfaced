/**
 * The canon proposal queue.
 *
 * The only route by which `WORLD.md` changes without a hand edit, and nothing changes
 * until an exact diff is approved. The classification is shown as advice and labelled
 * as such; the section a rule would join must be one the planner actually reads.
 */

import { useCallback, useEffect, useState } from "react";
import { useStyletron } from "baseui";
import { Button, KIND as BUTTON_KIND, SIZE } from "baseui/button";
import { Card, StyledBody } from "baseui/card";
import { Notification, KIND as NOTIFICATION_KIND } from "baseui/notification";
import { Select, type Value } from "baseui/select";
import { Tag, HIERARCHY, KIND as TAG_KIND, type TagKind } from "baseui/tag";
import { Textarea } from "baseui/textarea";
import { LabelSmall, LabelXSmall, ParagraphSmall, ParagraphXSmall } from "baseui/typography";

import {
  ApiError,
  approveProposal,
  classifyProposal,
  fetchCanonProposals,
  fetchProposalDiff,
  rejectProposal,
  type CanonProposal,
  type ProposalClassification,
  type ProposalDiff,
} from "../api/client";

const CLASSIFICATION_LABELS: Record<ProposalClassification, string> = {
  already_covered: "Already covered",
  genuine_addition: "Genuine addition",
  refinement: "Refinement",
  contradiction: "Contradiction",
  too_specific: "Too specific",
};

const CLASSIFICATION_KINDS: Record<ProposalClassification, TagKind> = {
  already_covered: TAG_KIND.neutral,
  genuine_addition: TAG_KIND.positive,
  refinement: TAG_KIND.accent,
  contradiction: TAG_KIND.negative,
  too_specific: TAG_KIND.neutral,
};

function messageFor(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}

function ProposalCard({
  proposal,
  onChanged,
}: {
  proposal: CanonProposal;
  onChanged: () => void;
}): React.JSX.Element {
  const [css, theme] = useStyletron();
  const [target, setTarget] = useState<Value>(
    proposal.target_heading
      ? [{ id: proposal.target_heading, label: proposal.target_heading }]
      : [],
  );
  const [note, setNote] = useState("");
  const [diff, setDiff] = useState<ProposalDiff | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const chosen = typeof target[0]?.id === "string" ? target[0].id : null;
  const decided = proposal.status !== "pending";

  const act = useCallback(
    (action: () => Promise<unknown>, fallback: string) => {
      setBusy(true);
      setError(null);
      action()
        .then(() => {
          onChanged();
        })
        .catch((caught: unknown) => {
          setError(messageFor(caught, fallback));
        })
        .finally(() => {
          setBusy(false);
        });
    },
    [onChanged],
  );

  return (
    <div
      className={css({
        borderTopWidth: "1px",
        borderTopStyle: "solid",
        borderTopColor: theme.colors.borderOpaque,
        paddingTop: theme.sizing.scale600,
        marginTop: theme.sizing.scale600,
      })}
    >
      <div
        className={css({
          display: "flex",
          gap: theme.sizing.scale300,
          flexWrap: "wrap",
          alignItems: "center",
          marginBottom: theme.sizing.scale400,
        })}
      >
        {proposal.classification && (
          <Tag
            closeable={false}
            kind={CLASSIFICATION_KINDS[proposal.classification]}
            hierarchy={HIERARCHY.secondary}
          >
            {CLASSIFICATION_LABELS[proposal.classification]}
          </Tag>
        )}
        <Tag
          closeable={false}
          kind={proposal.status === "applied" ? TAG_KIND.positive : TAG_KIND.neutral}
          hierarchy={HIERARCHY.secondary}
        >
          {proposal.status}
        </Tag>
        {proposal.classification && (
          <ParagraphXSmall marginTop={0} marginBottom={0} color={theme.colors.contentTertiary}>
            Advice. You decide.
          </ParagraphXSmall>
        )}
      </div>

      <ParagraphSmall marginTop={0}>{proposal.proposed_text}</ParagraphSmall>

      {proposal.classification_reason && (
        <ParagraphXSmall marginTop={0} color={theme.colors.contentSecondary}>
          {proposal.classification_reason}
        </ParagraphXSmall>
      )}

      {decided ? (
        <ParagraphXSmall color={theme.colors.contentTertiary}>
          {proposal.status === "applied"
            ? `Applied under ${proposal.target_heading ?? "canon"}.`
            : "Declined. WORLD.md is untouched."}
          {proposal.human_note ? ` Note: ${proposal.human_note}` : ""}
        </ParagraphXSmall>
      ) : (
        <div className={css({ display: "grid", gap: theme.sizing.scale400 })}>
          {!proposal.classification && (
            <div>
              <Button
                size={SIZE.mini}
                kind={BUTTON_KIND.tertiary}
                disabled={busy}
                onClick={() => {
                  act(() => classifyProposal(proposal.id), "The proposal could not be classified.");
                }}
              >
                Classify against canon
              </Button>
            </div>
          )}

          <div>
            <LabelXSmall>Section this rule would join</LabelXSmall>
            <Select
              options={proposal.allowed_headings.map((heading) => ({
                id: heading,
                label: heading,
              }))}
              value={target}
              onChange={(params) => {
                setTarget(params.value);
                setDiff(null);
              }}
              placeholder="Choose a section the planner reads"
              aria-label="Target section"
              clearable={false}
            />
            <ParagraphXSmall marginBottom={0} color={theme.colors.contentTertiary}>
              Only these sections reach the planning model. A rule anywhere else would never affect
              generation.
            </ParagraphXSmall>
          </div>

          {chosen && (
            <div>
              <Button
                size={SIZE.mini}
                kind={BUTTON_KIND.secondary}
                disabled={busy}
                onClick={() => {
                  setBusy(true);
                  setError(null);
                  fetchProposalDiff(proposal.id, chosen)
                    .then(setDiff)
                    .catch((caught: unknown) => {
                      setError(messageFor(caught, "The diff could not be built."));
                    })
                    .finally(() => {
                      setBusy(false);
                    });
                }}
              >
                Show the exact change
              </Button>
            </div>
          )}

          {diff && (
            <pre
              className={css({
                ...theme.typography.MonoParagraphXSmall,
                backgroundColor: theme.colors.backgroundSecondary,
                padding: theme.sizing.scale500,
                borderRadius: theme.borders.radius300,
                whiteSpace: "pre-wrap",
                overflowX: "auto",
                marginTop: 0,
              })}
            >
              {diff.unified_diff}
            </pre>
          )}

          <Textarea
            value={note}
            onChange={(event) => {
              setNote(event.currentTarget.value);
            }}
            placeholder="Optional note recorded with your decision"
            aria-label="Decision note"
          />

          <div className={css({ display: "flex", gap: theme.sizing.scale300, flexWrap: "wrap" })}>
            <Button
              size={SIZE.compact}
              disabled={busy || !chosen || !diff}
              onClick={() => {
                if (!chosen) return;
                act(
                  () => approveProposal(proposal.id, { target_heading: chosen, note }),
                  "The rule could not be applied.",
                );
              }}
            >
              Apply this rule to canon
            </Button>
            <Button
              size={SIZE.compact}
              kind={BUTTON_KIND.secondary}
              disabled={busy}
              onClick={() => {
                act(
                  () => rejectProposal(proposal.id, { note }),
                  "The proposal could not be declined.",
                );
              }}
            >
              Decline
            </Button>
          </div>

          {!diff && chosen && (
            <ParagraphXSmall marginTop={0} marginBottom={0} color={theme.colors.contentTertiary}>
              Read the diff before applying. You are approving the exact wording, not a summary of
              it.
            </ParagraphXSmall>
          )}
        </div>
      )}

      {proposal.failure_detail && (
        <div className={css({ marginTop: theme.sizing.scale400 })}>
          <Notification kind={NOTIFICATION_KIND.warning}>{proposal.failure_detail}</Notification>
        </div>
      )}

      {error && (
        <div className={css({ marginTop: theme.sizing.scale400 })}>
          <Notification kind={NOTIFICATION_KIND.negative}>{error}</Notification>
        </div>
      )}
    </div>
  );
}

export function CanonProposals({ slug }: { slug: string }): React.JSX.Element | null {
  const [proposals, setProposals] = useState<CanonProposal[]>([]);
  const [loaded, setLoaded] = useState(false);

  const load = useCallback(
    async (signal?: AbortSignal): Promise<void> => {
      try {
        setProposals(await fetchCanonProposals(slug, signal));
      } catch {
        // A failure here must not hide the rest of the page.
      } finally {
        setLoaded(true);
      }
    },
    [slug],
  );

  useEffect(() => {
    const controller = new AbortController();
    // Fetching on mount: setState happens after an await, not during the effect.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load(controller.signal);
    return () => {
      controller.abort();
    };
  }, [load]);

  if (!loaded || proposals.length === 0) {
    return null;
  }

  return (
    <Card title="Proposed canon rules">
      <StyledBody>
        <LabelSmall>Nothing here has changed WORLD.md.</LabelSmall>
        <ParagraphSmall marginBottom={0}>
          A reviewer proposed these permanent rules. Each changes canon only when you approve its
          exact diff.
        </ParagraphSmall>

        {proposals.map((proposal) => (
          <ProposalCard
            key={proposal.id}
            proposal={proposal}
            onChanged={() => {
              void load();
            }}
          />
        ))}
      </StyledBody>
    </Card>
  );
}

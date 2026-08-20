/**
 * The canon proposal queue.
 *
 * The only route by which `WORLD.md` changes without a hand edit, and nothing changes
 * until an exact diff is approved. The classification is shown as advice and labelled
 * as such; the section a rule would join must be one the planner actually reads.
 */

import { useCallback, useEffect, useState } from "react";

import {
  Button,
  Card,
  LabelSmall,
  LabelXSmall,
  Notification,
  ParagraphSmall,
  ParagraphXSmall,
  Select,
  Tag,
  Textarea,
  type TagKind,
} from "./ui";

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
  already_covered: "neutral",
  genuine_addition: "positive",
  refinement: "accent",
  contradiction: "negative",
  too_specific: "neutral",
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
  const [target, setTarget] = useState<string>(proposal.target_heading ?? "");
  const [note, setNote] = useState("");
  const [diff, setDiff] = useState<ProposalDiff | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const chosen = target === "" ? null : target;
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
    <div className="mt-6 border-t border-ink/10 pt-6">
      <div className="mb-4 flex flex-wrap items-center gap-3">
        {proposal.classification && (
          <Tag kind={CLASSIFICATION_KINDS[proposal.classification]}>
            {CLASSIFICATION_LABELS[proposal.classification]}
          </Tag>
        )}
        <Tag kind={proposal.status === "applied" ? "positive" : "neutral"}>
          {proposal.status}
        </Tag>
        {proposal.classification && (
          <ParagraphXSmall className="text-ink/50">Advice. You decide.</ParagraphXSmall>
        )}
      </div>

      <ParagraphSmall>{proposal.proposed_text}</ParagraphSmall>

      {proposal.classification_reason && (
        <ParagraphXSmall className="text-ink/70">{proposal.classification_reason}</ParagraphXSmall>
      )}

      {decided ? (
        <ParagraphXSmall className="text-ink/50">
          {proposal.status === "applied"
            ? `Applied under ${proposal.target_heading ?? "canon"}.`
            : "Declined. WORLD.md is untouched."}
          {proposal.human_note ? ` Note: ${proposal.human_note}` : ""}
        </ParagraphXSmall>
      ) : (
        <div className="grid gap-4">
          {!proposal.classification && (
            <div>
              <Button
                size="compact"
                variant="ghost"
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
            <LabelXSmall className="block">Section this rule would join</LabelXSmall>
            <Select
              options={proposal.allowed_headings.map((heading) => ({
                value: heading,
                label: heading,
              }))}
              value={target}
              onChange={(value) => {
                setTarget(value);
                setDiff(null);
              }}
              placeholder="Choose a section the planner reads"
              aria-label="Target section"
            />
            <ParagraphXSmall className="text-ink/50">
              Only these sections reach the planning model. A rule anywhere else would never affect
              generation.
            </ParagraphXSmall>
          </div>

          {chosen && (
            <div>
              <Button
                size="compact"
                variant="secondary"
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
            <pre className="overflow-x-auto rounded-[var(--radius-input)] bg-paper-2 p-5 font-mono text-[12px] leading-relaxed whitespace-pre-wrap text-ink/70">
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

          <div className="flex flex-wrap gap-3">
            <Button
              size="compact"
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
              size="compact"
              variant="secondary"
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
            <ParagraphXSmall className="text-ink/50">
              Read the diff before applying. You are approving the exact wording, not a summary of
              it.
            </ParagraphXSmall>
          )}
        </div>
      )}

      {proposal.failure_detail && (
        <div className="mt-4">
          <Notification kind="warning">{proposal.failure_detail}</Notification>
        </div>
      )}

      {error && (
        <div className="mt-4">
          <Notification kind="negative">{error}</Notification>
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
      <LabelSmall>Nothing here has changed WORLD.md.</LabelSmall>
      <ParagraphSmall>
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
    </Card>
  );
}

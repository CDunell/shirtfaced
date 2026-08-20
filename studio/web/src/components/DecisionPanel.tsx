/**
 * The owner's decision on one attempt.
 *
 * A decision is final, so every action asks for confirmation first and the controls
 * disable once one is recorded. The four downstream outcomes — database, documents,
 * reference, Git — are reported separately, because they cannot succeed or fail
 * together and a decision stands even when a later step did not.
 */

import { useCallback, useState } from "react";

import {
  Button,
  Checkbox,
  LabelSmall,
  Notification,
  ParagraphSmall,
  ParagraphXSmall,
  Tag,
  Textarea,
  type TagKind,
} from "./ui";

import {
  ApiError,
  approveAttempt,
  rejectAttempt,
  requestVariation,
  type Attempt,
  type DecisionResult,
  type DecisionSummary,
  type SyncState,
} from "../api/client";

type Pending = "approve" | "reject" | "variation" | null;

const DECISION_LABELS = {
  approved: "Approved",
  rejected: "Rejected",
  variation_requested: "Variation requested",
} as const;

const SYNC_LABELS: Record<SyncState, string> = {
  not_attempted: "not attempted",
  succeeded: "done",
  failed: "failed",
};

function SyncTag({ label, state }: { label: string; state: SyncState }): React.JSX.Element {
  const kind: TagKind =
    state === "succeeded" ? "positive" : state === "failed" ? "negative" : "neutral";
  return <Tag kind={kind}>{`${label}: ${SYNC_LABELS[state]}`}</Tag>;
}

function DecidedSummary({ decision }: { decision: DecisionSummary }): React.JSX.Element {
  return (
    <div className="mt-5">
      <div className="flex flex-wrap gap-2">
        <Tag kind="accent">{DECISION_LABELS[decision.decision]}</Tag>
        <SyncTag label="Documents" state={decision.markdown_sync} />
        <SyncTag label="Git" state={decision.git_sync} />
      </div>

      {decision.reason && <ParagraphSmall>Reason: {decision.reason}</ParagraphSmall>}
      {decision.note && <ParagraphSmall>Note: {decision.note}</ParagraphSmall>}
      {decision.instruction && <ParagraphSmall>Instruction: {decision.instruction}</ParagraphSmall>}

      {decision.reconciliation_required && (
        <div className="mt-4">
          <Notification kind="warning">
            The decision is recorded and final, but something downstream did not follow:{" "}
            {decision.reconciliation_detail ?? "see the audit log"}. Fix that, then re-run the step.
            Nothing has been rolled back.
          </Notification>
        </div>
      )}
    </div>
  );
}

export interface DecisionPanelProps {
  attempt: Attempt;
  onDecided: () => void;
}

export function DecisionPanel({ attempt, onDecided }: DecisionPanelProps): React.JSX.Element {
  const [pending, setPending] = useState<Pending>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const [note, setNote] = useState("");
  const [instruction, setInstruction] = useState("");
  const [promote, setPromote] = useState(false);

  const run = useCallback(
    (action: () => Promise<DecisionResult>) => {
      setBusy(true);
      setError(null);
      action()
        .then(() => {
          setPending(null);
          onDecided();
        })
        .catch((caught: unknown) => {
          setError(
            caught instanceof ApiError ? caught.message : "The decision could not be recorded.",
          );
        })
        .finally(() => {
          setBusy(false);
        });
    },
    [onDecided],
  );

  if (attempt.decision) {
    return <DecidedSummary decision={attempt.decision} />;
  }

  if (attempt.state !== "awaiting_decision") {
    return (
      <ParagraphXSmall className="text-ink/50">
        This attempt is {attempt.state.replace(/_/g, " ")} and cannot be decided.
      </ParagraphXSmall>
    );
  }

  const confirm = (
    <div className="flex flex-wrap gap-3">
      <Button
        size="compact"
        variant="primary"
        disabled={busy}
        onClick={() => {
          if (pending === "approve") {
            run(() => approveAttempt(attempt.id, { promote_to_reference: promote, note }));
          } else if (pending === "reject") {
            run(() => rejectAttempt(attempt.id, { reason }));
          } else if (pending === "variation") {
            run(() => requestVariation(attempt.id, { instruction }));
          }
        }}
      >
        Confirm — this is final
      </Button>
      <Button
        size="compact"
        variant="ghost"
        disabled={busy}
        onClick={() => {
          setPending(null);
          setError(null);
        }}
      >
        Cancel
      </Button>
    </div>
  );

  return (
    <div className="mt-6">
      <LabelSmall className="mb-3">Your decision</LabelSmall>

      {pending === null && (
        <div className="flex flex-wrap gap-3">
          <Button
            size="compact"
            onClick={() => {
              setPending("approve");
            }}
          >
            Approve
          </Button>
          <Button
            size="compact"
            variant="secondary"
            onClick={() => {
              setPending("reject");
            }}
          >
            Reject
          </Button>
          <Button
            size="compact"
            variant="ghost"
            onClick={() => {
              setPending("variation");
            }}
          >
            Request variation
          </Button>
        </div>
      )}

      {pending === "approve" && (
        <div className="grid gap-4">
          <Textarea
            value={note}
            onChange={(event) => {
              setNote(event.currentTarget.value);
            }}
            placeholder="Optional note recorded in the continuity ledger"
            aria-label="Approval note"
          />
          <Checkbox
            checked={promote}
            onChange={(checked) => {
              setPromote(checked);
            }}
          >
            Promote to reference
          </Checkbox>
          {confirm}
        </div>
      )}

      {pending === "reject" && (
        <div className="grid gap-4">
          <Textarea
            value={reason}
            onChange={(event) => {
              setReason(event.currentTarget.value);
            }}
            placeholder="Why is this wrong? This becomes the rejected-drift record."
            aria-label="Rejection reason"
            aria-invalid={reason.trim().length === 0}
          />
          <ParagraphXSmall className="text-ink/50">
            A reason is required. It is recorded verbatim and reaches the planner.
          </ParagraphXSmall>
          {reason.trim().length > 0 && confirm}
        </div>
      )}

      {pending === "variation" && (
        <div className="grid gap-4">
          <Textarea
            value={instruction}
            onChange={(event) => {
              setInstruction(event.currentTarget.value);
            }}
            placeholder="What should change in the next take?"
            aria-label="Variation instruction"
            aria-invalid={instruction.trim().length === 0}
          />
          <ParagraphXSmall className="text-ink/50">
            Records the request only. No image is generated until you continue the world.
          </ParagraphXSmall>
          {instruction.trim().length > 0 && confirm}
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

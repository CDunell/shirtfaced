/**
 * The owner's decision on one attempt.
 *
 * A decision is final, so every action asks for confirmation first and the controls
 * disable once one is recorded. The four downstream outcomes — database, documents,
 * reference, Git — are reported separately, because they cannot succeed or fail
 * together and a decision stands even when a later step did not.
 */

import { useCallback, useState } from "react";
import { useStyletron } from "baseui";
import { Button, KIND as BUTTON_KIND, SIZE } from "baseui/button";
import { Checkbox } from "baseui/checkbox";
import { Notification, KIND as NOTIFICATION_KIND } from "baseui/notification";
import { Tag, HIERARCHY, KIND as TAG_KIND } from "baseui/tag";
import { Textarea } from "baseui/textarea";
import { LabelSmall, ParagraphSmall, ParagraphXSmall } from "baseui/typography";

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
  return (
    <Tag
      closeable={false}
      kind={
        state === "succeeded"
          ? TAG_KIND.positive
          : state === "failed"
            ? TAG_KIND.negative
            : TAG_KIND.neutral
      }
      hierarchy={HIERARCHY.secondary}
    >
      {`${label}: ${SYNC_LABELS[state]}`}
    </Tag>
  );
}

function DecidedSummary({ decision }: { decision: DecisionSummary }): React.JSX.Element {
  const [css, theme] = useStyletron();

  return (
    <div className={css({ marginTop: theme.sizing.scale500 })}>
      <div className={css({ display: "flex", flexWrap: "wrap", gap: theme.sizing.scale200 })}>
        <Tag closeable={false} kind={TAG_KIND.primary} hierarchy={HIERARCHY.primary}>
          {DECISION_LABELS[decision.decision]}
        </Tag>
        <SyncTag label="Documents" state={decision.markdown_sync} />
        <SyncTag label="Git" state={decision.git_sync} />
      </div>

      {decision.reason && (
        <ParagraphSmall marginBottom={0}>Reason: {decision.reason}</ParagraphSmall>
      )}
      {decision.note && <ParagraphSmall marginBottom={0}>Note: {decision.note}</ParagraphSmall>}
      {decision.instruction && (
        <ParagraphSmall marginBottom={0}>Instruction: {decision.instruction}</ParagraphSmall>
      )}

      {decision.reconciliation_required && (
        <div className={css({ marginTop: theme.sizing.scale400 })}>
          <Notification
            kind={NOTIFICATION_KIND.warning}
            overrides={{ Body: { style: { width: "auto" } } }}
          >
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
  const [css, theme] = useStyletron();
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
      <ParagraphXSmall color={theme.colors.contentTertiary}>
        This attempt is {attempt.state.replace(/_/g, " ")} and cannot be decided.
      </ParagraphXSmall>
    );
  }

  const confirm = (
    <div className={css({ display: "flex", gap: theme.sizing.scale300, flexWrap: "wrap" })}>
      <Button
        size={SIZE.compact}
        kind={BUTTON_KIND.primary}
        disabled={busy}
        isLoading={busy}
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
        size={SIZE.compact}
        kind={BUTTON_KIND.tertiary}
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
    <div className={css({ marginTop: theme.sizing.scale600 })}>
      <LabelSmall marginBottom={theme.sizing.scale300}>Your decision</LabelSmall>

      {pending === null && (
        <div className={css({ display: "flex", gap: theme.sizing.scale300, flexWrap: "wrap" })}>
          <Button
            size={SIZE.compact}
            onClick={() => {
              setPending("approve");
            }}
          >
            Approve
          </Button>
          <Button
            size={SIZE.compact}
            kind={BUTTON_KIND.secondary}
            onClick={() => {
              setPending("reject");
            }}
          >
            Reject
          </Button>
          <Button
            size={SIZE.compact}
            kind={BUTTON_KIND.tertiary}
            onClick={() => {
              setPending("variation");
            }}
          >
            Request variation
          </Button>
        </div>
      )}

      {pending === "approve" && (
        <div className={css({ display: "grid", gap: theme.sizing.scale400 })}>
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
            onChange={(event) => {
              setPromote(event.currentTarget.checked);
            }}
          >
            Promote to reference
          </Checkbox>
          {confirm}
        </div>
      )}

      {pending === "reject" && (
        <div className={css({ display: "grid", gap: theme.sizing.scale400 })}>
          <Textarea
            value={reason}
            onChange={(event) => {
              setReason(event.currentTarget.value);
            }}
            placeholder="Why is this wrong? This becomes the rejected-drift record."
            aria-label="Rejection reason"
            error={reason.trim().length === 0}
          />
          <ParagraphXSmall marginTop={0} marginBottom={0} color={theme.colors.contentTertiary}>
            A reason is required. It is recorded verbatim and reaches the planner.
          </ParagraphXSmall>
          {reason.trim().length > 0 && confirm}
        </div>
      )}

      {pending === "variation" && (
        <div className={css({ display: "grid", gap: theme.sizing.scale400 })}>
          <Textarea
            value={instruction}
            onChange={(event) => {
              setInstruction(event.currentTarget.value);
            }}
            placeholder="What should change in the next take?"
            aria-label="Variation instruction"
            error={instruction.trim().length === 0}
          />
          <ParagraphXSmall marginTop={0} marginBottom={0} color={theme.colors.contentTertiary}>
            Records the request only. No image is generated until you continue the world.
          </ParagraphXSmall>
          {instruction.trim().length > 0 && confirm}
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

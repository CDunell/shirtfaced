/**
 * Continue World, and the attempts it produces.
 *
 * This is the one control in the application that spends money, so it says what it
 * will cost before it is pressed, and says plainly afterwards that a generated image
 * is not an approved one.
 */

import { useCallback, useEffect, useState } from "react";
import {
  Button,
  Card,
  LabelSmall,
  MonoLabelXSmall,
  Notification,
  ParagraphSmall,
  ParagraphXSmall,
  Tag,
  type TagKind,
} from "./ui";

import { DecisionPanel } from "./DecisionPanel";
import { ReviewPanel } from "./ReviewPanel";

import {
  ApiError,
  continueWorld,
  fetchAttempts,
  retryReview,
  type Attempt,
  type AttemptState,
} from "../api/client";

type Status = { kind: "idle" } | { kind: "generating" } | { kind: "failed"; message: string };

const STATE_LABELS: Record<AttemptState, string> = {
  planned: "Planned",
  prompt_ready: "Prompt ready",
  generating: "Generating",
  generated: "Generated",
  reviewing: "Reviewing",
  awaiting_decision: "Awaiting decision",
  approved: "Approved",
  rejected: "Rejected",
  failed: "Failed",
};

const STATE_KINDS: Record<AttemptState, TagKind> = {
  planned: "neutral",
  prompt_ready: "neutral",
  generating: "accent",
  generated: "positive",
  reviewing: "accent",
  awaiting_decision: "warning",
  approved: "positive",
  rejected: "negative",
  failed: "negative",
};

function AttemptCard({
  attempt,
  onReviewed,
}: {
  attempt: Attempt;
  onReviewed: () => void;
}): React.JSX.Element {
  const [reviewing, setReviewing] = useState(false);
  const [reviewError, setReviewError] = useState<string | null>(null);

  const review = useCallback(() => {
    setReviewing(true);
    setReviewError(null);
    retryReview(attempt.id)
      .then(() => {
        onReviewed();
      })
      .catch((error: unknown) => {
        setReviewError(error instanceof ApiError ? error.message : "The review could not be run.");
      })
      .finally(() => {
        setReviewing(false);
      });
  }, [attempt.id, onReviewed]);

  return (
    <div className="mt-6 border-t border-ink/10 pt-6">
      <div className="mb-4 flex flex-wrap items-center gap-4">
        <LabelSmall>
          Attempt {attempt.attempt_number} — {attempt.shot.external_id}
        </LabelSmall>
        <Tag kind={STATE_KINDS[attempt.state]}>{STATE_LABELS[attempt.state]}</Tag>
        {!attempt.approved && attempt.state === "generated" && (
          <ParagraphXSmall className="text-ink/50">
            Not approved — approval arrives with human decisions.
          </ParagraphXSmall>
        )}
      </div>

      {/* The full image opens in the same tab. Chrome and Edge both block
          target="_blank" under their pop-up settings, so it did not open at
          all; back returns to the panel. */}
      {attempt.image_url ? (
        <a href={attempt.image_url} rel="noreferrer">
          <img
            src={attempt.thumbnail_url ?? attempt.image_url}
            alt={`Generated image for ${attempt.shot.external_id}, ${attempt.shot.title}`}
            className="block h-auto max-w-full rounded-[var(--radius-img)]"
          />
        </a>
      ) : (
        attempt.failure_message && (
          <Notification kind="negative">
            {attempt.failure_code}: {attempt.failure_message}
          </Notification>
        )
      )}

      <dl className="mt-5 mb-0 grid grid-cols-[auto_1fr] gap-x-5 gap-y-1">
        {(
          [
            ["Hero product", attempt.hero_product],
            ["Camera", attempt.camera_position],
            ["Model", attempt.image_model],
            ["Size", attempt.image_size],
            ["Canon", attempt.world_document_hash?.slice(0, 12)],
          ] as [string, string | null | undefined][]
        )
          .filter(([, value]) => value)
          .map(([label, value]) => (
            <div key={label} className="contents">
              <dt className="text-[11px] font-semibold tracking-wide text-ink/60 uppercase">
                {label}
              </dt>
              <dd className="m-0">
                <MonoLabelXSmall className="text-ink/70">{value}</MonoLabelXSmall>
              </dd>
            </div>
          ))}
      </dl>

      {attempt.review && <ReviewPanel review={attempt.review} />}

      <DecisionPanel attempt={attempt} onDecided={onReviewed} />

      {attempt.image_url && (
        <div className="mt-5">
          <Button size="compact" variant="ghost" onClick={review} disabled={reviewing}>
            {reviewing ? "Reviewing…" : attempt.review ? "Review again" : "Review this image"}
          </Button>
          <ParagraphXSmall className="text-ink/50">
            Reviews the stored image. Never regenerates it.
          </ParagraphXSmall>
        </div>
      )}

      {reviewError && (
        <div className="mt-4">
          <Notification kind="negative">{reviewError}</Notification>
        </div>
      )}

      {attempt.production_prompt && (
        <details className="mt-5">
          <summary className="cursor-pointer text-[11px] font-semibold tracking-wide text-ink/60 uppercase">
            Production prompt
          </summary>
          <pre className="mt-2 overflow-x-auto rounded-[var(--radius-input)] bg-paper-2 p-5 font-mono text-[12px] leading-relaxed whitespace-pre-wrap text-ink/70">
            {attempt.production_prompt}
          </pre>
        </details>
      )}
    </div>
  );
}

export interface GenerationPanelProps {
  slug: string;
  /** Raised after a successful generation so the page can refresh what it shows. */
  onGenerated?: () => void;
}

export function GenerationPanel({ slug, onGenerated }: GenerationPanelProps): React.JSX.Element {
  const [status, setStatus] = useState<Status>({ kind: "idle" });
  const [attempts, setAttempts] = useState<Attempt[]>([]);
  const [live, setLive] = useState<boolean | null>(null);

  const load = useCallback(
    async (signal?: AbortSignal): Promise<void> => {
      try {
        setAttempts(await fetchAttempts(slug, signal));
      } catch {
        // History is supplementary; a failure to load it must not hide the action.
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

  const generate = useCallback(() => {
    setStatus({ kind: "generating" });
    continueWorld(slug)
      .then((result) => {
        setStatus({ kind: "idle" });
        setLive(result.live);
        void load();
        onGenerated?.();
      })
      .catch((error: unknown) => {
        setStatus({
          kind: "failed",
          message: error instanceof ApiError ? error.message : "The image could not be generated.",
        });
      });
  }, [slug, load, onGenerated]);

  const busy = status.kind === "generating";

  return (
    <Card title="Continue World">
      <ParagraphSmall>
        Generates exactly one image for the next shot, then waits for you. Nothing is approved
        automatically.
      </ParagraphSmall>

      <div className="mt-6">
        <Button size="compact" variant="primary" onClick={generate} disabled={busy}>
          {busy ? "Generating…" : "Continue World"}
        </Button>
      </div>

      {live === false && (
        <div className="mt-6">
          <Notification kind="info">
            Generated locally by the deterministic image client. No OpenAI request was made and
            nothing was billed. Set OPENAI_API_KEY and OPENAI_IMAGE_MODEL to use the real model.
          </Notification>
        </div>
      )}

      {status.kind === "failed" && (
        <div className="mt-6">
          <Notification kind="negative">{status.message}</Notification>
        </div>
      )}

      {attempts.length === 0 ? (
        <ParagraphXSmall className="text-ink/50">No attempts yet.</ParagraphXSmall>
      ) : (
        attempts.map((attempt) => (
          <AttemptCard
            key={attempt.id}
            attempt={attempt}
            onReviewed={() => {
              void load();
            }}
          />
        ))
      )}
    </Card>
  );
}

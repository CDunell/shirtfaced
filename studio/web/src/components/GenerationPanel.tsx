/**
 * Continue World, and the attempts it produces.
 *
 * This is the one control in the application that spends money, so it says what it
 * will cost before it is pressed, and says plainly afterwards that a generated image
 * is not an approved one.
 */

import { useCallback, useEffect, useState } from "react";
import { useStyletron } from "baseui";
import { Button, KIND as BUTTON_KIND, SIZE } from "baseui/button";
import { Card, StyledBody } from "baseui/card";
import { Notification, KIND as NOTIFICATION_KIND } from "baseui/notification";
import { Tag, HIERARCHY, KIND as TAG_KIND, type TagKind } from "baseui/tag";
import { LabelSmall, MonoLabelXSmall, ParagraphSmall, ParagraphXSmall } from "baseui/typography";

import {
  ApiError,
  continueWorld,
  fetchAttempts,
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
  planned: TAG_KIND.neutral,
  prompt_ready: TAG_KIND.neutral,
  generating: TAG_KIND.accent,
  generated: TAG_KIND.positive,
  reviewing: TAG_KIND.accent,
  awaiting_decision: TAG_KIND.warning,
  approved: TAG_KIND.positive,
  rejected: TAG_KIND.negative,
  failed: TAG_KIND.negative,
};

function AttemptCard({ attempt }: { attempt: Attempt }): React.JSX.Element {
  const [css, theme] = useStyletron();

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
          alignItems: "center",
          gap: theme.sizing.scale400,
          flexWrap: "wrap",
          marginBottom: theme.sizing.scale400,
        })}
      >
        <LabelSmall>
          Attempt {attempt.attempt_number} — {attempt.shot.external_id}
        </LabelSmall>
        <Tag closeable={false} kind={STATE_KINDS[attempt.state]} hierarchy={HIERARCHY.secondary}>
          {STATE_LABELS[attempt.state]}
        </Tag>
        {!attempt.approved && attempt.state === "generated" && (
          <ParagraphXSmall marginTop={0} marginBottom={0} color={theme.colors.contentTertiary}>
            Not approved — approval arrives with human decisions.
          </ParagraphXSmall>
        )}
      </div>

      {attempt.image_url ? (
        <a href={attempt.image_url} target="_blank" rel="noreferrer">
          <img
            src={attempt.thumbnail_url ?? attempt.image_url}
            alt={`Generated image for ${attempt.shot.external_id}, ${attempt.shot.title}`}
            className={css({
              maxWidth: "100%",
              height: "auto",
              display: "block",
              borderRadius: theme.borders.radius300,
            })}
          />
        </a>
      ) : (
        attempt.failure_message && (
          <Notification kind={NOTIFICATION_KIND.negative}>
            {attempt.failure_code}: {attempt.failure_message}
          </Notification>
        )
      )}

      <dl
        className={css({
          display: "grid",
          gridTemplateColumns: "auto 1fr",
          gap: `${theme.sizing.scale100} ${theme.sizing.scale500}`,
          marginTop: theme.sizing.scale500,
          marginBottom: 0,
        })}
      >
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
            <div key={label} className={css({ display: "contents" })}>
              <dt className={css({ ...theme.typography.LabelXSmall })}>{label}</dt>
              <dd className={css({ margin: 0 })}>
                <MonoLabelXSmall color={theme.colors.contentSecondary}>{value}</MonoLabelXSmall>
              </dd>
            </div>
          ))}
      </dl>

      {attempt.production_prompt && (
        <details className={css({ marginTop: theme.sizing.scale500 })}>
          <summary className={css({ ...theme.typography.LabelXSmall, cursor: "pointer" })}>
            Production prompt
          </summary>
          <pre
            className={css({
              ...theme.typography.MonoParagraphXSmall,
              backgroundColor: theme.colors.backgroundSecondary,
              padding: theme.sizing.scale500,
              borderRadius: theme.borders.radius300,
              whiteSpace: "pre-wrap",
              overflowX: "auto",
            })}
          >
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
  const [css, theme] = useStyletron();
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
      <StyledBody>
        <ParagraphSmall marginTop={0}>
          Generates exactly one image for the next shot, then waits for you. Nothing is approved
          automatically.
        </ParagraphSmall>

        <div className={css({ marginTop: theme.sizing.scale600 })}>
          <Button
            size={SIZE.compact}
            kind={BUTTON_KIND.primary}
            onClick={generate}
            disabled={busy}
            isLoading={busy}
          >
            {busy ? "Generating…" : "Continue World"}
          </Button>
        </div>

        {live === false && (
          <div className={css({ marginTop: theme.sizing.scale600 })}>
            <Notification
              kind={NOTIFICATION_KIND.info}
              overrides={{ Body: { style: { width: "auto" } } }}
            >
              Generated locally by the deterministic image client. No OpenAI request was made and
              nothing was billed. Set OPENAI_API_KEY and OPENAI_IMAGE_MODEL to use the real model.
            </Notification>
          </div>
        )}

        {status.kind === "failed" && (
          <div className={css({ marginTop: theme.sizing.scale600 })}>
            <Notification kind={NOTIFICATION_KIND.negative}>{status.message}</Notification>
          </div>
        )}

        {attempts.length === 0 ? (
          <ParagraphXSmall color={theme.colors.contentTertiary}>No attempts yet.</ParagraphXSmall>
        ) : (
          attempts.map((attempt) => <AttemptCard key={attempt.id} attempt={attempt} />)
        )}
      </StyledBody>
    </Card>
  );
}

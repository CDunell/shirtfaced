/**
 * Pick a world, pick a scene, get the prompts.
 *
 * This is the screen the tool is actually used through. Generation happens
 * elsewhere — in a browser, on a phone — so the job here is to produce the prompt
 * the canon implies and make it trivial to copy. Nothing is generated, no attempt is
 * recorded and no world is locked.
 *
 * Built for a phone first. The copy button is the product.
 */

import { useCallback, useEffect, useState } from "react";
import { useStyletron } from "baseui";
import { Button, KIND as BUTTON_KIND, SIZE } from "baseui/button";
import { Card, StyledBody } from "baseui/card";
import { Notification, KIND as NOTIFICATION_KIND } from "baseui/notification";
import { Select, type Value } from "baseui/select";
import { Tag, KIND as TAG_KIND } from "baseui/tag";
import { HeadingSmall, LabelSmall, ParagraphXSmall } from "baseui/typography";

import {
  ApiError,
  fetchWorld,
  fetchWorlds,
  writePrompts,
  type Prompts,
  type Shot,
  type WorldSummary,
} from "../api/client";

const STATUS_LABEL: Record<string, string> = {
  planned: "planned",
  in_progress: "in progress",
  approved: "approved",
  rejected: "rejected",
  abandoned: "abandoned",
};

function shotLabel(shot: Shot): string {
  const parts = [shot.external_id, shot.title];
  const detail = [shot.hero_product, shot.camera_position].filter(Boolean).join(" · ");
  return detail ? `${parts.join(" — ")}  (${detail})` : parts.join(" — ");
}

/** A prompt with a copy button. Selecting by hand on a phone is miserable. */
function PromptBlock({ title, text }: { title: string; text: string }): React.JSX.Element {
  const [css, theme] = useStyletron();
  const [copied, setCopied] = useState(false);

  const copy = useCallback(() => {
    // Older mobile browsers have no clipboard API; the textarea is still selectable.
    void navigator.clipboard.writeText(text).then(
      () => {
        setCopied(true);
      },
      () => {
        setCopied(false);
      },
    );
  }, [text]);

  useEffect(() => {
    if (!copied) return undefined;
    const timer = setTimeout(() => {
      setCopied(false);
    }, 2000);
    return () => {
      clearTimeout(timer);
    };
  }, [copied]);

  return (
    <div className={css({ marginTop: theme.sizing.scale700 })}>
      <div
        className={css({
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: theme.sizing.scale400,
          marginBottom: theme.sizing.scale300,
        })}
      >
        <LabelSmall>{title}</LabelSmall>
        <Button size={SIZE.compact} kind={BUTTON_KIND.secondary} onClick={copy}>
          {copied ? "Copied" : "Copy"}
        </Button>
      </div>
      <textarea
        readOnly
        value={text}
        rows={14}
        className={css({
          width: "100%",
          boxSizing: "border-box",
          padding: theme.sizing.scale500,
          borderRadius: theme.borders.radius300,
          border: `1px solid ${theme.colors.borderOpaque}`,
          backgroundColor: theme.colors.backgroundSecondary,
          color: theme.colors.contentPrimary,
          fontFamily: theme.typography.MonoParagraphSmall.fontFamily,
          fontSize: "13px",
          lineHeight: "1.5",
          resize: "vertical",
        })}
      />
    </div>
  );
}

export function PromptWorkbench(): React.JSX.Element {
  const [css, theme] = useStyletron();

  const [worlds, setWorlds] = useState<WorldSummary[]>([]);
  const [world, setWorld] = useState<Value>([]);
  const [shots, setShots] = useState<Shot[]>([]);
  const [shot, setShot] = useState<Value>([]);
  const [prompts, setPrompts] = useState<Prompts | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const slug = world[0]?.id ? String(world[0].id) : null;

  useEffect(() => {
    const controller = new AbortController();
    fetchWorlds(controller.signal)
      .then((found) => {
        setWorlds(found);
        const only = found.length === 1 ? found[0] : undefined;
        if (only) setWorld([{ id: only.slug, label: only.name }]);
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) setError(describe(cause));
      });
    return () => {
      controller.abort();
    };
  }, []);

  useEffect(() => {
    if (!slug) return undefined;
    const controller = new AbortController();
    fetchWorld(slug, controller.signal)
      .then((detail) => {
        setShots([...detail.shots].sort((a, b) => a.sequence - b.sequence));
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) setError(describe(cause));
      });
    return () => {
      controller.abort();
    };
  }, [slug]);

  const generate = useCallback(() => {
    if (!slug) return;
    setBusy(true);
    setError(null);
    const named = shot[0]?.id ? String(shot[0].id) : undefined;
    writePrompts(slug, named)
      .then(setPrompts)
      .catch((cause: unknown) => {
        setError(describe(cause));
      })
      .finally(() => {
        setBusy(false);
      });
  }, [slug, shot]);

  return (
    <div className={css({ maxWidth: "760px", margin: "0 auto" })}>
      <HeadingSmall marginTop={0}>Prompts</HeadingSmall>
      <ParagraphXSmall color={theme.colors.contentTertiary} marginTop={0}>
        Writes the prompt the canon implies. Generates nothing, records nothing, locks nothing.
      </ParagraphXSmall>

      {error && (
        <Notification
          kind={NOTIFICATION_KIND.negative}
          overrides={{ Body: { style: { width: "auto" } } }}
        >
          {error}
        </Notification>
      )}

      <Card>
        <StyledBody>
          <LabelSmall marginBottom={theme.sizing.scale300}>World</LabelSmall>
          <Select
            options={worlds.map((item) => ({ id: item.slug, label: item.name }))}
            value={world}
            placeholder="Choose a world"
            clearable={false}
            onChange={({ value }) => {
              // Reset here rather than in an effect: changing world invalidates the
              // scene and anything already written for it.
              setWorld(value);
              setShots([]);
              setShot([]);
              setPrompts(null);
            }}
          />

          <div className={css({ marginTop: theme.sizing.scale600 })}>
            <LabelSmall marginBottom={theme.sizing.scale300}>Scene</LabelSmall>
            <Select
              options={shots.map((item) => ({
                id: item.external_id,
                label: shotLabel(item),
                disabled: item.disabled,
              }))}
              value={shot}
              placeholder="Next planned shot"
              disabled={!slug}
              onChange={({ value }) => {
                setShot(value);
              }}
            />
            <ParagraphXSmall color={theme.colors.contentTertiary} marginBottom={0}>
              Leave empty for the next planned shot. Naming an approved one plans it again, which is
              how a variant is made.
            </ParagraphXSmall>
          </div>

          <Button
            onClick={generate}
            disabled={!slug || busy}
            isLoading={busy}
            overrides={{ Root: { style: { width: "100%", marginTop: theme.sizing.scale700 } } }}
          >
            Write prompts
          </Button>
        </StyledBody>
      </Card>

      {prompts && (
        <Card overrides={{ Root: { style: { marginTop: theme.sizing.scale600 } } }}>
          <StyledBody>
            <div
              className={css({
                display: "flex",
                alignItems: "center",
                gap: theme.sizing.scale300,
                flexWrap: "wrap",
              })}
            >
              <LabelSmall>
                {prompts.shot.external_id} — {prompts.shot.title}
              </LabelSmall>
              <Tag closeable={false} kind={TAG_KIND.neutral}>
                {STATUS_LABEL[prompts.shot.status] ?? prompts.shot.status}
              </Tag>
              {!prompts.live && (
                <Tag closeable={false} kind={TAG_KIND.warning}>
                  fake — nothing billed
                </Tag>
              )}
            </div>
            <ParagraphXSmall color={theme.colors.contentTertiary} marginBottom={0}>
              {prompts.shot.hero_product} · {prompts.shot.camera_position}
            </ParagraphXSmall>

            <PromptBlock title="Image prompt" text={prompts.image_prompt} />
            <PromptBlock
              title="Video prompt — upload the frame, paste this"
              text={prompts.video_prompt}
            />
          </StyledBody>
        </Card>
      )}
    </div>
  );
}

function describe(cause: unknown): string {
  if (cause instanceof ApiError) return cause.message;
  return "Something went wrong writing the prompts.";
}

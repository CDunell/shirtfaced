/**
 * Pick a world, pick a scene, get the prompts.
 *
 * This is the screen the tool is actually used through. Generation happens
 * elsewhere — in a browser, on a phone — so the job here is to produce the prompt
 * the canon implies and make it trivial to copy. No image is generated, no attempt is
 * recorded and no world is locked.
 *
 * Choosing a scene shows what has already been written for it. Writing again adds a
 * variation and leaves the earlier ones alone: a variation you cannot put beside the
 * one it varies from is not much of a variation.
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
import { LabelSmall, ParagraphXSmall } from "baseui/typography";

import { PageTitle } from "./chrome";

import {
  ApiError,
  fetchPromptHistory,
  fetchWorld,
  fetchWorlds,
  uploadPhoto,
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

/**
 * The photograph this prompt produced.
 *
 * The frames are generated elsewhere and brought back, so the upload is the only
 * moment anybody knows which prompt made which picture. Asking later is a memory
 * test, and the answer stops being available the moment there are two variations.
 */
function UploadTheResult({ promptId }: { promptId: string }): React.JSX.Element {
  const [css, theme] = useStyletron();
  const [state, setState] = useState<"idle" | "working" | "done" | "failed">("idle");
  const [message, setMessage] = useState<string | null>(null);
  const inputId = `upload-for-${promptId}`;

  const onFile = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;
      setState("working");
      setMessage(null);
      uploadPhoto(file, promptId)
        .then(() => {
          setState("done");
        })
        .catch((cause: unknown) => {
          setState("failed");
          setMessage(cause instanceof ApiError ? cause.message : "The upload failed.");
        })
        .finally(() => {
          event.target.value = "";
        });
    },
    [promptId],
  );

  return (
    <div className={css({ marginTop: theme.sizing.scale600 })}>
      <Button
        size={SIZE.compact}
        kind={BUTTON_KIND.secondary}
        disabled={state === "working"}
        onClick={() => document.getElementById(inputId)?.click()}
      >
        {state === "working"
          ? "Uploading…"
          : state === "done"
            ? "Uploaded — add another"
            : "Upload the photo this made"}
      </Button>
      <input
        id={inputId}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        onChange={onFile}
        className={css({ display: "none" })}
      />
      <ParagraphXSmall color={theme.colors.contentTertiary} marginBottom={0}>
        {state === "done"
          ? "It is in the print bench, tagged with this prompt."
          : (message ?? "Goes to the print bench, remembering it came from this prompt.")}
      </ParagraphXSmall>
    </div>
  );
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
  // Tagged with the scene it belongs to, so choosing another scene shows nothing
  // rather than the previous one's prompts, without an effect reaching in to clear
  // anything.
  const [history, setHistory] = useState<{ shot: string; items: Prompts[] }>({
    shot: "",
    items: [],
  });
  const [busy, setBusy] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const slug = world[0]?.id ? String(world[0].id) : null;
  const named = shot[0]?.id ? String(shot[0].id) : undefined;
  // A named scene shows only its own prompts. With none named, whatever was last
  // written is what there is to show.
  const variations = !named || history.shot === named ? history.items : [];

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

  // What already exists for the chosen scene. Without a scene there is nothing to
  // show: which shot is next is not settled until the prompt is written.
  useEffect(() => {
    if (!slug || !named) return undefined;
    const controller = new AbortController();
    // After an await, not during the effect: the request has already left.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoadingHistory(true);
    fetchPromptHistory(slug, named, controller.signal)
      .then((found) => {
        setHistory({ shot: named, items: found.variations });
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) setError(describe(cause));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoadingHistory(false);
      });
    return () => {
      controller.abort();
    };
  }, [slug, named]);

  const generate = useCallback(() => {
    if (!slug) return;
    setBusy(true);
    setError(null);
    writePrompts(slug, named)
      .then((written) => {
        // Prepended rather than refetched, so what was just asked for is on screen
        // immediately. A write with no scene chosen can land on a different shot
        // than the list is showing, in which case the list starts again.
        setHistory((existing) => ({
          shot: written.shot.external_id,
          items:
            existing.shot === written.shot.external_id ? [written, ...existing.items] : [written],
        }));
      })
      .catch((cause: unknown) => {
        setError(describe(cause));
      })
      .finally(() => {
        setBusy(false);
      });
  }, [slug, named]);

  return (
    <div className={css({ maxWidth: "760px", margin: "0 auto" })}>
      <PageTitle>Prompts</PageTitle>
      <ParagraphXSmall color={theme.colors.contentTertiary} marginTop={0}>
        Writes the prompt the canon implies. Generates no image and locks nothing. Every prompt
        written is kept, so a variation sits beside the one it varies from.
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
              setHistory({ shot: "", items: [] });
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
              Leave empty for the next planned shot. Choosing one shows what has already been
              written for it; writing again adds a variation.
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

      {loadingHistory && (
        <ParagraphXSmall color={theme.colors.contentTertiary}>
          Looking up what exists…
        </ParagraphXSmall>
      )}

      {!loadingHistory && named && variations.length === 0 && (
        <ParagraphXSmall color={theme.colors.contentTertiary}>
          Nothing has been written for this scene yet.
        </ParagraphXSmall>
      )}

      {variations.map((item) => (
        <Card
          key={`${item.shot.external_id}-${String(item.variation)}`}
          overrides={{ Root: { style: { marginTop: theme.sizing.scale600 } } }}
        >
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
                {item.shot.external_id} — {item.shot.title}
              </LabelSmall>
              <Tag closeable={false} kind={TAG_KIND.accent}>
                {item.variation === 1 ? "original" : `variation ${String(item.variation)}`}
              </Tag>
              <Tag closeable={false} kind={TAG_KIND.neutral}>
                {STATUS_LABEL[item.shot.status] ?? item.shot.status}
              </Tag>
              {!item.live && (
                <Tag closeable={false} kind={TAG_KIND.warning}>
                  fake — nothing billed
                </Tag>
              )}
            </div>
            <ParagraphXSmall color={theme.colors.contentTertiary} marginBottom={0}>
              {item.shot.hero_product} · {item.shot.camera_position} · written {writtenAt(item)}
            </ParagraphXSmall>

            <PromptBlock title="Image prompt" text={item.image_prompt} />
            <PromptBlock
              title="Video prompt — upload the frame, paste this"
              text={item.video_prompt}
            />

            {item.id && <UploadTheResult promptId={item.id} />}
          </StyledBody>
        </Card>
      ))}
    </div>
  );
}

/** Local date and time: these are read on the day they are written. */
function writtenAt(item: Prompts): string {
  const at = new Date(item.written_at);
  return Number.isNaN(at.getTime())
    ? "just now"
    : at.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function describe(cause: unknown): string {
  if (cause instanceof ApiError) return cause.message;
  return "Something went wrong writing the prompts.";
}

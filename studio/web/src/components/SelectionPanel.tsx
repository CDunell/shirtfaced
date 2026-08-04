/**
 * Next-shot selection and the production prompt preview.
 *
 * Selection is deterministic and free: it calls no model. The preview builds the
 * prompt without generating anything, and says plainly whether a billable model was
 * involved.
 */

import { useCallback, useEffect, useState } from "react";
import { useStyletron } from "baseui";
import { Button, KIND as BUTTON_KIND, SIZE } from "baseui/button";
import { Card, StyledBody } from "baseui/card";
import { Notification, KIND as NOTIFICATION_KIND } from "baseui/notification";
import { Tag, HIERARCHY, KIND as TAG_KIND } from "baseui/tag";
import { LabelSmall, ParagraphSmall, ParagraphXSmall } from "baseui/typography";

import {
  ApiError,
  fetchNextShot,
  previewPlan,
  type NextShot,
  type PlanPreview,
} from "../api/client";

type Selection =
  { kind: "loading" } | { kind: "loaded"; next: NextShot } | { kind: "failed"; message: string };

type Preview =
  | { kind: "idle" }
  | { kind: "working" }
  | { kind: "ready"; preview: PlanPreview }
  | { kind: "failed"; message: string };

function messageFor(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}

function PlanDetail({ preview }: { preview: PlanPreview }): React.JSX.Element {
  const [css, theme] = useStyletron();
  const { plan } = preview;

  const rows: [string, string][] = [
    ["Scene", plan.scene_summary],
    ["Emotional beat", plan.emotional_beat],
    ["Hero product", plan.hero_product],
    ["Product visibility", plan.product_visibility_instruction],
    ["Camera", plan.camera_position],
    ["Lighting", plan.lighting_source],
    ["Documentary imperfection", plan.documentary_imperfection],
  ];

  return (
    <div className={css({ marginTop: theme.sizing.scale600 })}>
      {!preview.live && (
        <div className={css({ marginBottom: theme.sizing.scale600 })}>
          <Notification
            kind={NOTIFICATION_KIND.info}
            overrides={{ Body: { style: { width: "auto" } } }}
          >
            Built by the deterministic planner. No OpenAI request was made and nothing was billed.
            Set OPENAI_API_KEY and OPENAI_TEXT_MODEL to use the real model.
          </Notification>
        </div>
      )}

      <LabelSmall marginBottom={theme.sizing.scale300}>Production prompt</LabelSmall>
      <pre
        className={css({
          ...theme.typography.MonoParagraphXSmall,
          backgroundColor: theme.colors.backgroundSecondary,
          padding: theme.sizing.scale600,
          borderRadius: theme.borders.radius300,
          whiteSpace: "pre-wrap",
          overflowX: "auto",
          marginTop: 0,
        })}
      >
        {plan.production_prompt}
      </pre>

      <dl className={css({ display: "grid", gap: theme.sizing.scale300, margin: 0 })}>
        {rows.map(([label, value]) => (
          <div key={label} className={css({ display: "grid", gap: theme.sizing.scale100 })}>
            <dt className={css({ ...theme.typography.LabelXSmall })}>{label}</dt>
            <dd
              className={css({
                ...theme.typography.ParagraphSmall,
                margin: 0,
                color: theme.colors.contentSecondary,
              })}
            >
              {value}
            </dd>
          </div>
        ))}
      </dl>

      <LabelSmall marginTop={theme.sizing.scale600} marginBottom={theme.sizing.scale300}>
        Negative constraints
      </LabelSmall>
      <div className={css({ display: "flex", flexWrap: "wrap", gap: theme.sizing.scale200 })}>
        {plan.negative_constraints.map((constraint) => (
          <Tag
            key={constraint}
            closeable={false}
            kind={TAG_KIND.negative}
            hierarchy={HIERARCHY.secondary}
          >
            {constraint}
          </Tag>
        ))}
      </div>

      <LabelSmall marginTop={theme.sizing.scale600} marginBottom={theme.sizing.scale300}>
        Australian authenticity anchors
      </LabelSmall>
      <div className={css({ display: "flex", flexWrap: "wrap", gap: theme.sizing.scale200 })}>
        {plan.australian_authenticity_anchors.map((anchor) => (
          <Tag
            key={anchor}
            closeable={false}
            kind={TAG_KIND.neutral}
            hierarchy={HIERARCHY.secondary}
          >
            {anchor}
          </Tag>
        ))}
      </div>
    </div>
  );
}

export function SelectionPanel({ slug }: { slug: string }): React.JSX.Element {
  const [css, theme] = useStyletron();
  const [selection, setSelection] = useState<Selection>({ kind: "loading" });
  const [preview, setPreview] = useState<Preview>({ kind: "idle" });

  const load = useCallback(
    async (signal?: AbortSignal): Promise<void> => {
      try {
        setSelection({ kind: "loaded", next: await fetchNextShot(slug, signal) });
      } catch (error: unknown) {
        if (signal?.aborted) return;
        setSelection({
          kind: "failed",
          message: messageFor(error, "The selection could not be loaded."),
        });
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

  const requestPreview = useCallback(() => {
    setPreview({ kind: "working" });
    previewPlan(slug)
      .then((result) => {
        setPreview({ kind: "ready", preview: result });
      })
      .catch((error: unknown) => {
        setPreview({
          kind: "failed",
          message: messageFor(error, "The prompt could not be built."),
        });
      });
  }, [slug]);

  if (selection.kind === "loading") {
    return (
      <Card title="Next shot">
        <StyledBody>
          <ParagraphSmall marginTop={0}>Working out which shot comes next…</ParagraphSmall>
        </StyledBody>
      </Card>
    );
  }

  if (selection.kind === "failed") {
    return <Notification kind={NOTIFICATION_KIND.negative}>{selection.message}</Notification>;
  }

  const { next } = selection;

  return (
    <Card title="Next shot">
      <StyledBody>
        {next.selected ? (
          <>
            <LabelSmall marginBottom={theme.sizing.scale300}>
              {next.selected.external_id} — {next.selected.title}
            </LabelSmall>
            <div
              className={css({
                display: "flex",
                flexWrap: "wrap",
                gap: theme.sizing.scale200,
                marginBottom: theme.sizing.scale500,
              })}
            >
              <Tag closeable={false} kind={TAG_KIND.accent} hierarchy={HIERARCHY.secondary}>
                {next.selected.hero_product ?? "product unset"}
              </Tag>
              <Tag closeable={false} kind={TAG_KIND.accent} hierarchy={HIERARCHY.secondary}>
                {next.selected.camera_position ?? "camera unset"}
              </Tag>
            </div>
          </>
        ) : (
          <LabelSmall marginBottom={theme.sizing.scale400}>No shot can be selected</LabelSmall>
        )}

        <LabelSmall marginBottom={theme.sizing.scale200}>Why</LabelSmall>
        <ParagraphSmall marginTop={0} color={theme.colors.contentSecondary}>
          {next.reason}
        </ParagraphSmall>

        {next.set_aside.length > 0 && (
          <details className={css({ marginTop: theme.sizing.scale400 })}>
            <summary className={css({ ...theme.typography.LabelXSmall, cursor: "pointer" })}>
              {next.set_aside.length} shot{next.set_aside.length === 1 ? "" : "s"} set aside
            </summary>
            <ul
              className={css({
                ...theme.typography.ParagraphXSmall,
                color: theme.colors.contentSecondary,
                paddingLeft: theme.sizing.scale800,
              })}
            >
              {next.set_aside.map((entry) => (
                <li key={`${entry.external_id}-${entry.reason}`}>
                  {entry.external_id}: {entry.reason}
                </li>
              ))}
            </ul>
          </details>
        )}

        {next.selected && (
          <div className={css({ marginTop: theme.sizing.scale600 })}>
            <Button
              size={SIZE.compact}
              kind={BUTTON_KIND.secondary}
              onClick={requestPreview}
              disabled={preview.kind === "working"}
            >
              {preview.kind === "working" ? "Building the prompt…" : "Preview production prompt"}
            </Button>
            <ParagraphXSmall marginBottom={0} color={theme.colors.contentTertiary}>
              Builds the prompt only. No image is generated and nothing is saved.
            </ParagraphXSmall>
          </div>
        )}

        {preview.kind === "failed" && (
          <div className={css({ marginTop: theme.sizing.scale600 })}>
            <Notification kind={NOTIFICATION_KIND.negative}>{preview.message}</Notification>
          </div>
        )}

        {preview.kind === "ready" && <PlanDetail preview={preview.preview} />}
      </StyledBody>
    </Card>
  );
}

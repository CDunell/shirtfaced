/**
 * Next-shot selection.
 *
 * Deterministic and free: it calls no model, and it explains the choice rather than
 * only announcing it. Writing the prompt for the chosen shot happens on the Prompts
 * page, which keeps what it writes.
 */

import { useCallback, useEffect, useState } from "react";
import { useStyletron } from "baseui";
import { Card, StyledBody } from "baseui/card";
import { Notification, KIND as NOTIFICATION_KIND } from "baseui/notification";
import { Tag, HIERARCHY, KIND as TAG_KIND } from "baseui/tag";
import { LabelSmall, ParagraphSmall, ParagraphXSmall } from "baseui/typography";

import { ApiError, fetchNextShot, type NextShot } from "../api/client";

type Selection =
  { kind: "loading" } | { kind: "loaded"; next: NextShot } | { kind: "failed"; message: string };

function messageFor(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}

export function SelectionPanel({ slug }: { slug: string }): React.JSX.Element {
  const [css, theme] = useStyletron();
  const [selection, setSelection] = useState<Selection>({ kind: "loading" });

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
          <ParagraphXSmall
            marginTop={theme.sizing.scale600}
            marginBottom={0}
            color={theme.colors.contentTertiary}
          >
            The prompt for this shot is written on the Prompts page, where it is kept.
          </ParagraphXSmall>
        )}
      </StyledBody>
    </Card>
  );
}

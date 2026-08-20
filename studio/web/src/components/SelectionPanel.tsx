/**
 * Next-shot selection.
 *
 * Deterministic and free: it calls no model, and it explains the choice rather than
 * only announcing it. Writing the prompt for the chosen shot happens on the Prompts
 * page, which keeps what it writes.
 */

import { useCallback, useEffect, useState } from "react";
import { Card, LabelSmall, Notification, ParagraphSmall, ParagraphXSmall, Tag } from "./ui";

import { ApiError, fetchNextShot, type NextShot } from "../api/client";

type Selection =
  { kind: "loading" } | { kind: "loaded"; next: NextShot } | { kind: "failed"; message: string };

function messageFor(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}

export function SelectionPanel({ slug }: { slug: string }): React.JSX.Element {
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
        <ParagraphSmall>Working out which shot comes next…</ParagraphSmall>
      </Card>
    );
  }

  if (selection.kind === "failed") {
    return <Notification kind="negative">{selection.message}</Notification>;
  }

  const { next } = selection;

  return (
    <Card title="Next shot">
      {next.selected ? (
        <>
          <LabelSmall className="mb-3 block">
            {next.selected.external_id} — {next.selected.title}
          </LabelSmall>
          <div className="mb-5 flex flex-wrap gap-2">
            <Tag kind="accent">{next.selected.hero_product ?? "product unset"}</Tag>
            <Tag kind="accent">{next.selected.camera_position ?? "camera unset"}</Tag>
          </div>
        </>
      ) : (
        <LabelSmall className="mb-4 block">No shot can be selected</LabelSmall>
      )}

      <LabelSmall className="mb-2 block">Why</LabelSmall>
      <ParagraphSmall className="text-ink/70">{next.reason}</ParagraphSmall>

      {next.set_aside.length > 0 && (
        <details className="mt-4">
          <summary className="cursor-pointer text-[11px] font-semibold tracking-wide uppercase text-ink/60">
            {next.set_aside.length} shot{next.set_aside.length === 1 ? "" : "s"} set aside
          </summary>
          <ul className="pl-8 text-[12px] leading-relaxed text-ink/70">
            {next.set_aside.map((entry) => (
              <li key={`${entry.external_id}-${entry.reason}`}>
                {entry.external_id}: {entry.reason}
              </li>
            ))}
          </ul>
        </details>
      )}

      {next.selected && (
        <ParagraphXSmall className="mt-6 text-ink/50">
          The prompt for this shot is written on the Prompts page, where it is kept.
        </ParagraphXSmall>
      )}
    </Card>
  );
}

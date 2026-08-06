"use client";

import { useActionState, useEffect, useState, useTransition } from "react";
import { Button, Card, Field, Select } from "@/components/ui";
import { readHistoryAction, writePromptsAction } from "@/app/prompts/actions";
import { EMPTY_PROMPTS } from "@/lib/prompt-state";
import type { StudioPrompts, StudioShot, StudioWorld } from "@/lib/studio";

/** A prompt with a copy button. Selecting several hundred words by hand on a phone
 *  is miserable, and copying is the only thing anyone does with this text. */
function PromptBlock({ title, text }: { title: string; text: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // No clipboard permission. The textarea is still selectable by hand.
      setCopied(false);
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between gap-3">
        <p className="text-[13px] font-semibold tracking-wide uppercase">{title}</p>
        <Button type="button" variant="ghost" onClick={copy}>
          {copied ? "Copied" : "Copy"}
        </Button>
      </div>
      <textarea
        readOnly
        value={text}
        rows={16}
        onFocus={(event) => event.currentTarget.select()}
        className="w-full rounded-[var(--radius-btn)] border border-ink/15 bg-paper-2 p-3 font-mono text-[12px] leading-relaxed"
      />
    </div>
  );
}

/** Local date and time: these are read on the day they are written. */
function writtenAt(value: string): string {
  const at = new Date(value);
  return Number.isNaN(at.getTime())
    ? "just now"
    : at.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export function PromptWorkbench({
  worlds,
  shotsByWorld,
}: {
  worlds: StudioWorld[];
  shotsByWorld: Record<string, StudioShot[]>;
}) {
  const [state, action, pending] = useActionState(writePromptsAction, {
    ...EMPTY_PROMPTS,
    world: worlds[0]?.slug ?? "",
  });
  const [world, setWorld] = useState(state.world || (worlds[0]?.slug ?? ""));
  const [shot, setShot] = useState("");
  const [variations, setVariations] = useState<StudioPrompts[]>([]);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [loadingHistory, startLoading] = useTransition();
  const shots = shotsByWorld[world] ?? [];

  // What already exists for the chosen scene. Without a scene there is nothing to
  // show: which shot is next is not settled until the prompt is written.
  useEffect(() => {
    if (!world || !shot) {
      setVariations([]);
      setHistoryError(null);
      return;
    }
    startLoading(async () => {
      const result = await readHistoryAction(world, shot);
      setVariations(result.variations);
      setHistoryError(result.error);
    });
  }, [world, shot]);

  // A freshly written prompt belongs at the top of the list it was added to. A
  // write with no scene chosen can land on a different shot than the list is
  // showing, in which case the list starts again.
  useEffect(() => {
    const written = state.prompts;
    if (!written) return;
    setVariations((existing) => {
      const showing = existing[0];
      if (showing?.shot.external_id !== written.shot.external_id) return [written];
      return showing.variation === written.variation
        ? existing
        : [written, ...existing];
    });
  }, [state.prompts]);

  return (
    <div className="flex flex-col gap-6">
      {state.error && (
        <Card className="border-coral bg-coral/10">
          <p className="text-[14px]">{state.error}</p>
        </Card>
      )}

      <Card>
        <form action={action} className="flex flex-col gap-4">
          <Field label="World" htmlFor="world">
            <Select
              id="world"
              name="world"
              value={world}
              onChange={(event) => setWorld(event.target.value)}
            >
              {worlds.map((item) => (
                <option key={item.slug} value={item.slug}>
                  {item.name}
                </option>
              ))}
            </Select>
          </Field>

          <Field
            label="Scene"
            htmlFor="shot"
            hint="Leave on the next planned shot, or pick one. Choosing one shows what has already been written for it; writing again adds a variation."
          >
            <Select
              id="shot"
              name="shot"
              value={shot}
              onChange={(event) => setShot(event.target.value)}
            >
              <option value="">Next planned shot</option>
              {shots.map((shot) => (
                <option key={shot.external_id} value={shot.external_id}>
                  {shot.external_id} — {shot.title}
                  {shot.hero_product ? ` (${shot.hero_product})` : ""}
                </option>
              ))}
            </Select>
          </Field>

          <Button type="submit" disabled={pending}>
            {pending ? "Writing…" : "Write prompts"}
          </Button>
        </form>
      </Card>

      {historyError && (
        <Card className="border-coral bg-coral/10">
          <p className="text-[14px]">{historyError}</p>
        </Card>
      )}

      {loadingHistory && <p className="text-[13px] text-ink/50">Looking up what exists…</p>}

      {!loadingHistory && shot && variations.length === 0 && (
        <p className="text-[13px] text-ink/50">Nothing has been written for this scene yet.</p>
      )}

      {variations.map((item) => (
        <Card
          key={`${item.shot.external_id}-${String(item.variation)}`}
          className="flex flex-col gap-6"
        >
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <p className="font-semibold">
                {item.shot.external_id} — {item.shot.title}
              </p>
              <span className="rounded-[10px] bg-ink px-2 py-0.5 text-[11px] font-semibold tracking-wide text-paper uppercase">
                {item.variation === 1 ? "original" : `variation ${String(item.variation)}`}
              </span>
            </div>
            <p className="mt-1 text-[13px] text-ink/50">
              {item.shot.hero_product} · {item.shot.camera_position} · written{" "}
              {writtenAt(item.written_at)}
              {!item.live && " · fake, nothing billed"}
            </p>
          </div>

          <PromptBlock title="Image prompt" text={item.image_prompt} />
          <PromptBlock
            title="Video prompt — upload the frame, paste this"
            text={item.video_prompt}
          />
        </Card>
      ))}
    </div>
  );
}

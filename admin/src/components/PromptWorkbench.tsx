"use client";

import { useActionState, useState } from "react";
import { Button, Card, Field, Select } from "@/components/ui";
import { writePromptsAction } from "@/app/prompts/actions";
import { EMPTY_PROMPTS } from "@/lib/prompt-state";
import type { StudioShot, StudioWorld } from "@/lib/studio";

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
  const shots = shotsByWorld[world] ?? [];

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
            hint="Leave on the next planned shot, or pick one. Choosing an approved shot plans it again, which is how a product-page variant is made."
          >
            <Select id="shot" name="shot" defaultValue="">
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

      {state.prompts && (
        <Card className="flex flex-col gap-6">
          <div>
            <p className="font-semibold">
              {state.prompts.shot.external_id} — {state.prompts.shot.title}
            </p>
            <p className="mt-1 text-[13px] text-ink/50">
              {state.prompts.shot.hero_product} · {state.prompts.shot.camera_position}
              {!state.prompts.live && " · fake, nothing billed"}
            </p>
          </div>

          <PromptBlock title="Image prompt" text={state.prompts.image_prompt} />
          <PromptBlock
            title="Video prompt — upload the frame, paste this"
            text={state.prompts.video_prompt}
          />
        </Card>
      )}
    </div>
  );
}

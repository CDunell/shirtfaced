"use server";

import { StudioUnavailable, writePrompts } from "@/lib/studio";
import { EMPTY_PROMPTS, type PromptsState } from "@/lib/prompt-state";

/**
 * Ask Studio for the prompts for one shot.
 *
 * Runs on the server, so the Studio URL and its OpenAI key never reach the browser.
 * Nothing is generated and nothing is recorded — this only writes text.
 *
 * A "use server" module may export nothing but async functions, which is why the
 * state type and its empty value live in lib/prompt-state.
 */
export async function writePromptsAction(
  _previous: PromptsState,
  formData: FormData,
): Promise<PromptsState> {
  const world = String(formData.get("world") ?? "").trim();
  const shot = String(formData.get("shot") ?? "").trim();

  if (!world) {
    return { ...EMPTY_PROMPTS, error: "Choose a world first." };
  }

  try {
    const prompts = await writePrompts(world, shot || undefined);
    return { prompts, error: null, world, shot };
  } catch (cause) {
    const error =
      cause instanceof StudioUnavailable
        ? cause.message
        : "Something went wrong asking Studio for the prompts.";
    return { prompts: null, error, world, shot };
  }
}

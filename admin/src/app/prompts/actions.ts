"use server";

import { fetchPromptHistory, StudioUnavailable, writePrompts } from "@/lib/studio";
import { EMPTY_PROMPTS, type HistoryResult, type PromptsState } from "@/lib/prompt-state";

/**
 * What has already been written for a scene.
 *
 * Called directly from the client when the scene changes, rather than through the
 * form, because choosing a scene is a question and not a submission. Costs nothing
 * and writes nothing.
 */
export async function readHistoryAction(
  world: string,
  shot: string,
): Promise<HistoryResult> {
  try {
    const history = await fetchPromptHistory(world, shot);
    return { variations: history.variations, error: null };
  } catch (cause) {
    return {
      variations: [],
      error:
        cause instanceof StudioUnavailable
          ? cause.message
          : "Something went wrong asking Studio what exists.",
    };
  }
}

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

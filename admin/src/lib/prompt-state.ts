/**
 * The Prompts form's state shape.
 *
 * Kept out of the `"use server"` module: a server-actions file may only export
 * async functions, so a constant or a type living beside the action stops the whole
 * page compiling.
 */

import type { StudioPrompts } from "@/lib/studio";

export interface PromptsState {
  prompts: StudioPrompts | null;
  error: string | null;
  /** Kept so the form still shows what was asked for after a failure. */
  world: string;
  shot: string;
}

/** The answer to "what has already been written for this scene?" */
export interface HistoryResult {
  variations: StudioPrompts[];
  error: string | null;
}

export const EMPTY_PROMPTS: PromptsState = {
  prompts: null,
  error: null,
  world: "",
  shot: "",
};

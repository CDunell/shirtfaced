/**
 * Talking to Shirtfaced Studio.
 *
 * Studio is a separate FastAPI service with its own database, the world documents on
 * disk and the OpenAI key. Admin never holds any of that: it asks Studio for a prompt
 * and shows the answer. Every call here runs on the server, so the Studio URL is not
 * exposed to the browser and no key ever leaves that service.
 */

import { cookies } from "next/headers";
import { SESSION_COOKIE } from "@/lib/session";

export interface StudioShot {
  external_id: string;
  sequence: number;
  title: string;
  hero_product: string | null;
  camera_position: string | null;
  status: string;
  disabled: boolean;
}

export interface StudioWorld {
  slug: string;
  name: string;
}

export interface StudioPrompts {
  shot: StudioShot;
  selection_reason: string;
  image_prompt: string;
  video_prompt: string;
  /** False when Studio's deterministic fake wrote these, so nothing was billed. */
  live: boolean;
}

export class StudioUnavailable extends Error {}

function baseUrl(): string {
  const url = process.env.STUDIO_API_URL ?? process.env.STUDIO_URL;
  if (!url) {
    throw new StudioUnavailable(
      "STUDIO_API_URL is not set, so admin cannot reach Studio.",
    );
  }
  return url.replace(/\/+$/, "");
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  // Studio requires the session admin issued. This call is made by the server,
  // not the browser, so the cookie has to be carried across by hand -- it is the
  // caller's own session, not a service account, so Studio is never reachable by
  // anyone who is not signed in here.
  const store = await cookies();
  const session = store.get(SESSION_COOKIE)?.value;

  let response: Response;
  try {
    response = await fetch(`${baseUrl()}${path}`, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(session ? { Cookie: `${SESSION_COOKIE}=${session}` } : {}),
        ...(init?.headers ?? {}),
      },
      // Prompts are written fresh every time; a cached one would be a lie about
      // what the current canon says.
      cache: "no-store",
    });
  } catch (cause) {
    throw new StudioUnavailable(
      "Studio could not be reached. It runs as its own service — check it is up.",
      { cause },
    );
  }

  if (!response.ok) {
    let detail = `Studio returned ${response.status}.`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // A non-JSON error body is not worth reporting over the status code.
    }
    throw new StudioUnavailable(detail);
  }
  return (await response.json()) as T;
}

export function fetchWorlds(): Promise<StudioWorld[]> {
  return call<StudioWorld[]>("/api/worlds");
}

export function fetchShots(slug: string): Promise<{ shots: StudioShot[] }> {
  return call<{ shots: StudioShot[] }>(`/api/worlds/${encodeURIComponent(slug)}`);
}

/**
 * Write both prompts for a shot. Generates no image and records nothing.
 *
 * Omit the shot for the next planned one. Naming a shot skips Studio's eligibility
 * rules, so an approved shot can be planned again for a product-page variant.
 */
export function writePrompts(slug: string, shot?: string): Promise<StudioPrompts> {
  const query = shot ? `?shot=${encodeURIComponent(shot)}` : "";
  return call<StudioPrompts>(
    `/api/worlds/${encodeURIComponent(slug)}/prompts${query}`,
    { method: "POST" },
  );
}

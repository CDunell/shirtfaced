/**
 * Typed client for the Studio API.
 *
 * The browser never holds an OpenAI key. Every model call happens server-side, so
 * this module only ever talks to our own FastAPI service on the same origin.
 */

export interface HealthResponse {
  status: string;
  version: string;
}

export type ShotStatus = "planned" | "in_progress" | "approved" | "rejected" | "abandoned";

export interface Shot {
  id: string;
  external_id: string;
  sequence: number;
  priority: number;
  title: string;
  hero_product: string | null;
  camera_position: string | null;
  lighting_source: string | null;
  status: ShotStatus;
  disabled: boolean;
  source_line: number | null;
}

export interface ShotCounts {
  total: number;
  planned: number;
  in_progress: number;
  approved: number;
  rejected: number;
  abandoned: number;
}

export interface WorldSummary {
  id: string;
  slug: string;
  name: string;
  status: "active" | "archived";
  world_document_hash: string | null;
  continuity_document_hash: string | null;
  shotlist_document_hash: string | null;
}

export interface WorldDetail extends WorldSummary {
  shots: Shot[];
  counts: ShotCounts;
  next_planned_shot: Shot | null;
}

export class ApiError extends Error {
  /** HTTP status, or 0 when the request never reached the service. */
  readonly status: number;

  constructor(status: number, message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "ApiError";
    this.status = status;
  }
}

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      headers: { Accept: "application/json" },
      ...(signal ? { signal } : {}),
    });
  } catch (cause) {
    throw new ApiError(0, "The Studio service could not be reached.", { cause });
  }

  if (!response.ok) {
    throw new ApiError(response.status, `The Studio service returned ${String(response.status)}.`);
  }

  return (await response.json()) as T;
}

/** Liveness only: this tells you the process is up, not that it is ready to work. */
export function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return getJson<HealthResponse>("/health", signal);
}

/** Worlds that have been imported into the database. */
export function fetchWorlds(signal?: AbortSignal): Promise<WorldSummary[]> {
  return getJson<WorldSummary[]>("/api/worlds", signal);
}

/** One world with its shotlist. */
export function fetchWorld(slug: string, signal?: AbortSignal): Promise<WorldDetail> {
  return getJson<WorldDetail>(`/api/worlds/${encodeURIComponent(slug)}`, signal);
}

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

export interface SetAside {
  external_id: string;
  reason: string;
}

export interface NextShot {
  selected: Shot | null;
  reason: string;
  eligible_count: number;
  set_aside: SetAside[];
  last_hero_product: string | null;
  last_camera_position: string | null;
}

export interface PromptPlan {
  scene_summary: string;
  emotional_beat: string;
  hero_product: string;
  product_visibility_instruction: string;
  camera_position: string;
  lighting_source: string;
  documentary_imperfection: string;
  australian_authenticity_anchors: string[];
  negative_constraints: string[];
  selection_rationale: string;
  production_prompt: string;
}

export interface PlanPreview {
  shot: Shot;
  selection_reason: string;
  plan: PromptPlan;
  /** False when the deterministic fake planner produced this, so nothing was billed. */
  live: boolean;
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

async function request<T>(path: string, method: string, signal?: AbortSignal): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      method,
      headers: { Accept: "application/json" },
      ...(signal ? { signal } : {}),
    });
  } catch (cause) {
    throw new ApiError(0, "The Studio service could not be reached.", { cause });
  }

  if (!response.ok) {
    // The API explains refusals in `detail`; showing that beats a bare status code.
    const detail = await response
      .clone()
      .json()
      .then((body: unknown) =>
        typeof body === "object" && body !== null && "detail" in body ? String(body.detail) : null,
      )
      .catch(() => null);

    throw new ApiError(
      response.status,
      detail ?? `The Studio service returned ${String(response.status)}.`,
    );
  }

  return (await response.json()) as T;
}

function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  return request<T>(path, "GET", signal);
}

function postJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  return request<T>(path, "POST", signal);
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

/** The deterministic selection and its explanation. Calls no model. */
export function fetchNextShot(slug: string, signal?: AbortSignal): Promise<NextShot> {
  return getJson<NextShot>(`/api/worlds/${encodeURIComponent(slug)}/next-shot`, signal);
}

/** Build the production prompt without generating anything. Development only. */
export function previewPlan(slug: string, signal?: AbortSignal): Promise<PlanPreview> {
  return postJson<PlanPreview>(`/api/worlds/${encodeURIComponent(slug)}/plan-preview`, signal);
}

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

export type AttemptState =
  | "planned"
  | "prompt_ready"
  | "generating"
  | "generated"
  | "reviewing"
  | "awaiting_decision"
  | "approved"
  | "rejected"
  | "failed";

export type FailureCode =
  | "planning_failed"
  | "provider_error"
  | "provider_timeout"
  | "provider_refused"
  | "invalid_image"
  | "storage_failed"
  | "configuration"
  | "internal";

export interface Attempt {
  id: string;
  attempt_number: number;
  state: AttemptState;
  shot: Shot;
  selection_reason: string | null;
  production_prompt: string | null;
  prompt_plan: PromptPlan | null;
  image_model: string | null;
  image_size: string | null;
  image_quality: string | null;
  provider_request_id: string | null;
  hero_product: string | null;
  camera_position: string | null;
  world_document_hash: string | null;
  shotlist_document_hash: string | null;
  failure_code: FailureCode | null;
  failure_message: string | null;
  parent_attempt_id: string | null;
  created_at: string;
  image_url: string | null;
  thumbnail_url: string | null;
  /** The most recent review, if the image has been reviewed. */
  review: Review | null;
  /** Present once decided. The controls are disabled when it is set. */
  decision: DecisionSummary | null;
  /** Generating an image is not approving it. */
  approved: boolean;
}

export type GateStatus = "PASS" | "FAIL" | "UNCERTAIN" | "NOT_APPLICABLE";

export type GateName =
  | "mood"
  | "australian_authenticity"
  | "product_visibility"
  | "third_party_branding"
  | "vehicle_continuity"
  | "wardrobe_balance"
  | "composition"
  | "documentary_credibility"
  | "story";

export interface GateResult {
  status: GateStatus;
  evidence: string;
  codes: string[];
  confidence: number;
  /** Whether this finding could change the recommendation. */
  material: boolean;
}

export type ReviewRecommendation =
  | "APPROVE_RECOMMENDED"
  | "APPROVE_WITH_NOTE_RECOMMENDED"
  | "REJECT_RECOMMENDED"
  | "REVIEW_UNCERTAIN";

export interface Review {
  id: string;
  review_model: string;
  recommendation: ReviewRecommendation;
  verdict: "approved" | "approved_with_note" | "rejected" | "uncertain";
  gates: Record<GateName, GateResult>;
  mood_score: number;
  australian_authenticity_score: number;
  product_visibility_score: number;
  documentary_credibility_score: number;
  story_score: number;
  branding_compliant: boolean;
  vehicle_compliant: boolean;
  strongest_success: string;
  material_drift: string | null;
  recommended_action: string | null;
  next_hero_product: string | null;
  next_camera: string | null;
  created_at: string;
  blocking_gates: GateName[];
  uncertain_gates: GateName[];
}

export type DecisionKind = "approved" | "rejected" | "variation_requested";
export type SyncState = "not_attempted" | "succeeded" | "failed";

export interface DecisionSummary {
  decision: DecisionKind;
  reason: string | null;
  note: string | null;
  instruction: string | null;
  promote_to_reference: boolean;
  markdown_sync: SyncState;
  git_sync: SyncState;
  git_commit: string | null;
  reconciliation_required: boolean;
  reconciliation_detail: string | null;
  created_at: string;
}

export interface DecisionResult {
  attempt_id: string;
  attempt_state: AttemptState;
  decision: DecisionKind;
  shot_external_id: string;
  shot_status: string;
  reason: string | null;
  note: string | null;
  instruction: string | null;
  promote_to_reference: boolean;
  /** Reported separately: these cannot succeed or fail together. */
  markdown_sync: SyncState;
  git_sync: SyncState;
  reference_sync: SyncState;
  git_commit: string | null;
  document_hashes: Record<string, string>;
  reconciliation_required: boolean;
  reconciliation: string[];
}

export type ProposalClassification =
  "already_covered" | "genuine_addition" | "refinement" | "contradiction" | "too_specific";

export type ProposalStatus = "pending" | "approved" | "rejected" | "applied" | "failed";

export interface CanonProposal {
  id: string;
  status: ProposalStatus;
  proposed_text: string;
  reason: string | null;
  human_note: string | null;
  /** Advisory. It orders the queue and explains; it never decides. */
  classification: ProposalClassification | null;
  classification_reason: string | null;
  classified_by: string | null;
  target_heading: string | null;
  reviewer_model: string | null;
  applied_wording: string | null;
  applied_at: string | null;
  failure_detail: string | null;
  git_commit: string | null;
  created_at: string;
  decided_at: string | null;
  /** The only sections a rule may join; anything else is invisible to the planner. */
  allowed_headings: string[];
}

export interface ProposalDiff {
  proposal_id: string;
  target_heading: string;
  unified_diff: string;
  applied_wording: string;
}

export interface GenerationResult {
  attempt: Attempt;
  /** Null when the review failed; the attempt records why and it can be retried. */
  review: Review | null;
  /** False when the deterministic fakes produced this, so nothing was billed. */
  live: boolean;
  review_live: boolean;
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

async function request<T>(
  path: string,
  method: string,
  signal?: AbortSignal,
  body?: unknown,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      method,
      headers: body
        ? { Accept: "application/json", "Content-Type": "application/json" }
        : { Accept: "application/json" },
      ...(body ? { body: JSON.stringify(body) } : {}),
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

function postJson<T>(path: string, signal?: AbortSignal, body?: unknown): Promise<T> {
  return request<T>(path, "POST", signal, body);
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

/** Generate one image for the next shot. Synchronous, and the expensive one. */
export function continueWorld(slug: string, signal?: AbortSignal): Promise<GenerationResult> {
  return postJson<GenerationResult>(`/api/worlds/${encodeURIComponent(slug)}/continue`, signal);
}

/** Attempts for a world, newest first. */
export function fetchAttempts(slug: string, signal?: AbortSignal): Promise<Attempt[]> {
  return getJson<Attempt[]>(`/api/worlds/${encodeURIComponent(slug)}/attempts`, signal);
}

/** Approve. Marks the shot approved and records it in the world documents. */
export function approveAttempt(
  attemptId: string,
  body: { promote_to_reference: boolean; note: string },
  signal?: AbortSignal,
): Promise<DecisionResult> {
  return postJson<DecisionResult>(
    `/api/attempts/${encodeURIComponent(attemptId)}/approve`,
    signal,
    body,
  );
}

/** Reject with a reason. The shot stays planned; the drift is recorded. */
export function rejectAttempt(
  attemptId: string,
  body: { reason: string },
  signal?: AbortSignal,
): Promise<DecisionResult> {
  return postJson<DecisionResult>(
    `/api/attempts/${encodeURIComponent(attemptId)}/reject`,
    signal,
    body,
  );
}

/** Ask for another take. Records intent; generates nothing. */
export function requestVariation(
  attemptId: string,
  body: { instruction: string },
  signal?: AbortSignal,
): Promise<DecisionResult> {
  return postJson<DecisionResult>(
    `/api/attempts/${encodeURIComponent(attemptId)}/variation`,
    signal,
    body,
  );
}

/** Canon proposals for a world. None of them has changed WORLD.md. */
export function fetchCanonProposals(slug: string, signal?: AbortSignal): Promise<CanonProposal[]> {
  return getJson<CanonProposal[]>(
    `/api/worlds/${encodeURIComponent(slug)}/canon-proposals`,
    signal,
  );
}

/** Weigh a proposal against canon. Advisory; changes nothing. */
export function classifyProposal(id: string, signal?: AbortSignal): Promise<CanonProposal> {
  return postJson<CanonProposal>(`/api/canon-proposals/${encodeURIComponent(id)}/classify`, signal);
}

/** The exact change a proposal would make. Nothing is written. */
export function fetchProposalDiff(
  id: string,
  targetHeading: string,
  signal?: AbortSignal,
): Promise<ProposalDiff> {
  const query = `?target_heading=${encodeURIComponent(targetHeading)}`;
  return getJson<ProposalDiff>(
    `/api/canon-proposals/${encodeURIComponent(id)}/diff${query}`,
    signal,
  );
}

/** Apply the diff to WORLD.md. The only write to permanent canon. */
export function approveProposal(
  id: string,
  body: { target_heading: string; note: string },
  signal?: AbortSignal,
): Promise<CanonProposal> {
  return postJson<CanonProposal>(
    `/api/canon-proposals/${encodeURIComponent(id)}/approve`,
    signal,
    body,
  );
}

/** Decline. WORLD.md is untouched. */
export function rejectProposal(
  id: string,
  body: { note: string },
  signal?: AbortSignal,
): Promise<CanonProposal> {
  return postJson<CanonProposal>(
    `/api/canon-proposals/${encodeURIComponent(id)}/reject`,
    signal,
    body,
  );
}

/** Review the existing image again. Adds a review; never regenerates. */
export function retryReview(attemptId: string, signal?: AbortSignal): Promise<Review> {
  return postJson<Review>(`/api/attempts/${encodeURIComponent(attemptId)}/retry-review`, signal);
}

/** Build the production prompt without generating anything. Development only. */
export function previewPlan(slug: string, signal?: AbortSignal): Promise<PlanPreview> {
  return postJson<PlanPreview>(`/api/worlds/${encodeURIComponent(slug)}/plan-preview`, signal);
}

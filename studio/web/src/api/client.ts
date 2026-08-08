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

function putJson<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
  return request<T>(path, "PUT", signal, body);
}

/** The service's own explanation of a refusal, for the calls that are not JSON. */
async function failure(response: Response): Promise<ApiError> {
  const detail = await response
    .clone()
    .json()
    .then((body: unknown) =>
      typeof body === "object" && body !== null && "detail" in body ? String(body.detail) : null,
    )
    .catch(() => null);
  return new ApiError(
    response.status,
    detail ?? `The Studio service returned ${String(response.status)}.`,
  );
}

export interface Prompts {
  id?: string;
  shot: Shot;
  selection_reason: string;
  image_prompt: string;
  video_prompt: string;
  live: boolean;
  /** 1 for the first prompt written for this shot, and up from there. */
  variation: number;
  written_at: string;
}

export interface PromptHistory {
  shot: Shot;
  /** Newest first. Empty for a shot nobody has planned yet. */
  variations: Prompts[];
}

/**
 * Write both prompts for a shot. Generates no image.
 *
 * Omit `shot` for the next eligible one. Naming a shot skips the selector's
 * eligibility rules, so an approved shot can be planned again for a variant.
 *
 * Each call adds a variation rather than replacing the one written last time.
 */
export function writePrompts(slug: string, shot?: string, signal?: AbortSignal): Promise<Prompts> {
  const query = shot ? `?shot=${encodeURIComponent(shot)}` : "";
  return postJson<Prompts>(`/api/worlds/${encodeURIComponent(slug)}/prompts${query}`, signal);
}

/** What has already been written for a shot. Writes nothing and costs nothing. */
export function fetchPromptHistory(
  slug: string,
  shot: string,
  signal?: AbortSignal,
): Promise<PromptHistory> {
  return getJson<PromptHistory>(
    `/api/worlds/${encodeURIComponent(slug)}/prompts?shot=${encodeURIComponent(shot)}`,
    signal,
  );
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

// --- printing ----------------------------------------------------------------

export interface Design {
  name: string;
}

export interface PromptLineage {
  shot_external_id: string;
  variation: number;
}

export interface Photo {
  id: string;
  url: string;
  label: string;
  /** False for anything Studio generated, true for anything brought in. */
  uploaded: boolean;
  width: number;
  height: number;
  placed: boolean;
  /** Null for a photograph nobody attributed to a prompt. */
  from_prompt: PromptLineage | null;
}

/** Clockwise from the top left, each 0..1 of the photograph. */
export type Corners = [number, number][];

export interface Placement {
  corners: Corners;
  settings: Record<string, number>;
  design: string | null;
}

export function fetchDesigns(signal?: AbortSignal): Promise<Design[]> {
  return getJson<Design[]>("/api/designs", signal);
}

export function fetchPhotos(signal?: AbortSignal): Promise<Photo[]> {
  return getJson<Photo[]>("/api/photos", signal);
}

/**
 * Bring in a photograph Studio did not make.
 *
 * `promptVariationId` records which prompt produced it. The frames are generated
 * elsewhere and brought back, so the upload is the only moment anybody knows.
 */
export async function uploadPhoto(file: File, promptVariationId?: string): Promise<Photo> {
  const body = new FormData();
  body.append("file", file);
  if (promptVariationId) body.append("prompt_variation_id", promptVariationId);
  const response = await fetch("/api/photos", { method: "POST", body });
  if (!response.ok) {
    throw await failure(response);
  }
  return (await response.json()) as Photo;
}

export function fetchPlacement(photoId: string, signal?: AbortSignal): Promise<Placement | null> {
  return getJson<Placement | null>(`/api/photos/${encodeURIComponent(photoId)}/placement`, signal);
}

export function savePlacement(
  photoId: string,
  placement: { corners: Corners; design?: string | null },
): Promise<Placement> {
  return putJson<Placement>(`/api/photos/${encodeURIComponent(photoId)}/placement`, placement);
}

/**
 * Render the design onto the photograph.
 *
 * Returns the image itself rather than a URL: nothing is stored until somebody
 * decides a render is the right one, so there is nothing to link to.
 */
export async function printPhoto(photoId: string, design: string): Promise<Blob> {
  const path = `/api/photos/${encodeURIComponent(photoId)}/print?design=${encodeURIComponent(design)}`;
  const response = await fetch(path, { method: "POST" });
  if (!response.ok) {
    throw await failure(response);
  }
  return await response.blob();
}

/** One hard gate's outcome, with the evidence the extractor decided it on. */
export interface DesignGate {
  gate: string;
  status: "pass" | "fail" | "not_tested";
  evidence: string;
}

/** One weighted category's computed points. */
export interface DesignCategory {
  category: string;
  rating: number;
  points: number;
  max_points: number;
  floor: number;
  below_floor: boolean;
}

export interface DesignScore {
  design_id: string;
  design_name: string;
  measurements: Record<string, unknown>;
  blocked: boolean;
  total_score: number;
  max_total_score: number;
  band: string;
  failed_gates: string[];
  untested_gates: string[];
  floor_failures: string[];
  gates: DesignGate[];
  categories: DesignCategory[];
  thresholds: Record<string, number>;
}

/** Measure a design image and score it against DESIGN_REVIEW_SCORECARD.md. */
export async function scoreDesign(file: File, designName?: string): Promise<DesignScore> {
  const body = new FormData();
  body.append("image", file);
  if (designName) body.append("design_name", designName);
  const response = await fetch("/api/design/score", { method: "POST", body });
  if (!response.ok) {
    throw await failure(response);
  }
  return (await response.json()) as DesignScore;
}

// --- Composing designs from the archive -------------------------------------

export interface ComposeBrief {
  seed: number;
  garment_key: string;
  primary_text: string;
  secondary_text: string;
  placement: string;
  fit: string;
  treatment: string;
  garment_colour: string;
  inks: number;
  limit: number;
}

export interface ComposedOption {
  grammar_key: string;
  grammar_name: string;
  reads_as: string;
  rationale: string;
  score: number;
  confidence: number;
  approvals: number;
  decisions: number;
  width_mm: number;
  height_mm: number;
  content_hash: string;
  parts: Record<string, string>;
  svg: string;
}

export interface StoredDesign {
  id: string;
  seed: number;
  garment_key: string;
  placement_key: string;
  grammar_key: string;
  state: AttemptState;
  width_mm: number;
  height_mm: number;
  content_hash: string;
  parts: Record<string, unknown>;
  decided_by: string;
  decision_note: string;
  svg: string;
}

/** Answer a brief. Stores nothing: looking is free and reversible. */
export async function composeDesign(
  brief: Partial<ComposeBrief> & { seed: number; garment_key: string },
  signal?: AbortSignal,
): Promise<ComposedOption[]> {
  return request<ComposedOption[]>("/api/compose", "POST", signal, brief);
}

/** Keep one option. The server recomposes rather than trusting posted artwork. */
export async function keepDesign(
  brief: Partial<ComposeBrief> & { seed: number; garment_key: string },
  grammarKey: string,
  signal?: AbortSignal,
): Promise<StoredDesign> {
  const query = new URLSearchParams({ grammar_key: grammarKey });
  return request<StoredDesign>(`/api/compose/designs?${query.toString()}`, "POST", signal, brief);
}

export async function listDesigns(state?: string, signal?: AbortSignal): Promise<StoredDesign[]> {
  const query = state ? `?${new URLSearchParams({ state }).toString()}` : "";
  return request<StoredDesign[]>(`/api/compose/designs${query}`, "GET", signal);
}

/** Settle a design. The name is required: an approval nobody signed is not one. */
export async function decideDesign(
  designId: string,
  approved: boolean,
  decidedBy: string,
  note = "",
  signal?: AbortSignal,
): Promise<StoredDesign> {
  return request<StoredDesign>(`/api/compose/designs/${designId}/decision`, "POST", signal, {
    approved,
    decided_by: decidedBy,
    note,
  });
}

export interface Reproducibility {
  reproducible: boolean;
  content_hash?: string;
  assembler_version: string;
  state?: string;
  awaiting?: boolean;
  reason?: string;
  detail?: string;
}

/** Rebuild a stored design from its brief and report whether the bytes match. */
export async function verifyDesign(
  designId: string,
  signal?: AbortSignal,
): Promise<Reproducibility> {
  return request<Reproducibility>(`/api/compose/designs/${designId}/verify`, "POST", signal);
}

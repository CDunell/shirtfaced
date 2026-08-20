/**
 * The design backlog.
 *
 * Concepts come from PostgreSQL, not from anyone's memory of the library file.
 * "Next" is a server answer; a decision needs a name; an approval is a
 * versioned milestone. The client only ever asks and shows.
 */

import { ApiError } from "./client";

export type ConceptStatus =
  "backlog" | "ready" | "exploring" | "approved" | "rejected" | "held" | "retired" | "superseded";

export type DesignAttemptState =
  | "planned"
  | "generating"
  | "generated"
  | "awaiting_decision"
  | "approved"
  | "rejected"
  | "variation_requested"
  | "failed";

export type DesignDecisionKind = "approved" | "rejected" | "variation_requested";

export type DesignAttemptMethod =
  "image_generation" | "deterministic_composition" | "manual_import" | "hybrid";

export interface DesignAssetView {
  id: string;
  kind: string;
  relative_path: string;
  sha256: string;
  mime_type: string;
  width: number | null;
  height: number | null;
  byte_size: number;
}

export interface DesignDecisionView {
  id: string;
  decision: DesignDecisionKind;
  reason: string | null;
  note: string | null;
  instruction: string | null;
  actor: string;
  created_at: string;
}

export interface ApprovedDesignView {
  id: string;
  version: number;
  approved_by: string;
  approved_at: string;
  superseded_at: string | null;
  master_asset_id: string;
  design_attempt_id: string;
}

export interface DesignAttemptView {
  id: string;
  concept_id: string;
  attempt_number: number;
  method: DesignAttemptMethod;
  state: DesignAttemptState;
  parent_attempt_id: string | null;
  created_at: string;
  assets: DesignAssetView[];
  decision: DesignDecisionView | null;
  approved_version: number | null;
  /** Why a failed attempt failed. A settled row otherwise looks identical to a
   * working one, and the drop zone invites artwork it will refuse. */
  failure_message: string | null;
}

export interface ConceptView {
  id: string;
  library: string;
  external_number: number;
  slug: string;
  title: string;
  concept_text: string;
  status: ConceptStatus;
  concept_kind: string;
  retirement: string;
  salvage: string;
  garments: string[];
  round: number;
  round_label: string;
  priority: number;
  tags: string[];
  treatment_lanes: string[];
  notes: string;
  attempt_count: number;
  latest_attempt_state: DesignAttemptState | null;
  approved_versions: number;
}

export interface ConceptDetailView extends ConceptView {
  attempts: DesignAttemptView[];
  versions: ApprovedDesignView[];
}

async function fail(response: Response): Promise<never> {
  const body = (await response
    .clone()
    .json()
    .catch(() => null)) as { detail?: unknown } | null;
  const detail = typeof body?.detail === "string" ? body.detail : null;
  throw new ApiError(
    response.status,
    detail ?? `The Studio service returned ${String(response.status)}.`,
  );
}

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");
  if (!(init?.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const response = await fetch(path, { ...init, headers });
  if (!response.ok) return await fail(response);
  return (await response.json()) as T;
}

export async function fetchConcepts(status?: ConceptStatus): Promise<ConceptView[]> {
  const suffix = status ? `?status=${encodeURIComponent(status)}` : "";
  return await json<ConceptView[]>(`/api/concepts${suffix}`);
}

export async function fetchNextConcept(): Promise<ConceptView | null> {
  try {
    return await json<ConceptView>("/api/concepts/next");
  } catch (cause) {
    if (cause instanceof ApiError && cause.status === 404) return null;
    throw cause;
  }
}

export async function fetchConcept(id: string): Promise<ConceptDetailView> {
  return await json<ConceptDetailView>(`/api/concepts/${encodeURIComponent(id)}`);
}

export async function fetchReviewQueue(): Promise<DesignAttemptView[]> {
  return await json<DesignAttemptView[]>("/api/concepts/queue");
}

export async function createAttempt(
  conceptId: string,
  method: DesignAttemptMethod,
): Promise<DesignAttemptView> {
  return await json<DesignAttemptView>(`/api/concepts/${encodeURIComponent(conceptId)}/attempts`, {
    method: "POST",
    body: JSON.stringify({ method }),
  });
}

export async function uploadAsset(
  attemptId: string,
  file: File,
  kind = "artwork",
): Promise<DesignAssetView> {
  const body = new FormData();
  body.append("file", file, file.name);
  body.append("kind", kind);
  return await json<DesignAssetView>(
    `/api/concepts/attempts/${encodeURIComponent(attemptId)}/assets`,
    { method: "POST", body },
  );
}

/** Close an attempt that will never be worked, with the reason recorded.
 *
 * An attempt only reaches `awaiting_decision` by having artwork submitted, so
 * one opened in error had no exit and no way off the queue but deletion. This
 * settles it and keeps the row, so the mistake stays legible. */
export async function abandonAttempt(
  attemptId: string,
  reason: string,
): Promise<DesignAttemptView> {
  return await json<DesignAttemptView>(
    `/api/concepts/attempts/${encodeURIComponent(attemptId)}/abandon`,
    { method: "POST", body: JSON.stringify({ reason }) },
  );
}

export async function submitAttempt(attemptId: string): Promise<DesignAttemptView> {
  return await json<DesignAttemptView>(
    `/api/concepts/attempts/${encodeURIComponent(attemptId)}/submit`,
    { method: "POST", body: "{}" },
  );
}

export async function decideAttempt(
  attemptId: string,
  decision: DesignDecisionKind,
  actor: string,
  words: { reason?: string; note?: string; instruction?: string } = {},
): Promise<DesignDecisionView> {
  return await json<DesignDecisionView>(
    `/api/concepts/attempts/${encodeURIComponent(attemptId)}/decision`,
    { method: "POST", body: JSON.stringify({ decision, actor, ...words }) },
  );
}

export async function approveDesign(
  attemptId: string,
  approvedBy: string,
): Promise<ApprovedDesignView> {
  return await json<ApprovedDesignView>(
    `/api/concepts/attempts/${encodeURIComponent(attemptId)}/approve-design`,
    { method: "POST", body: JSON.stringify({ approved_by: approvedBy }) },
  );
}

export function assetUrl(assetId: string): string {
  return `/api/concepts/assets/${encodeURIComponent(assetId)}`;
}

/* --- The scorecard ---------------------------------------------------------
 *
 * Every field below is what the server actually sends. The rubric is fetched
 * rather than restated here: thirteen gate ids and nine category maximums
 * written out a second time in TypeScript is the duplication the 14 August
 * port had to undo once already, and a drift between the two copies would be
 * invisible until something was approved that should not have been.
 *
 * Nothing in these types is required unless the server guarantees it. An
 * EvidenceRecord that declared fields required which 233 of 3,639 live records
 * did not have is why: the lint rule then removed the guard, and the page went
 * blank.
 */

export type ReviewResult = "pass" | "fail" | "not_tested";

export interface RubricGroup {
  id: string;
  label: string;
  blurb: string;
}

export interface RubricGate {
  id: string;
  label: string;
  question: string;
  group: string;
}

export interface RubricCategory {
  id: string;
  label: string;
  prompt: string;
  maximum: number;
  ratingFloor: number;
  minimumRequired: number;
  group: string;
}

export interface Rubric {
  groups: RubricGroup[];
  gates: RubricGate[];
  categories: RubricCategory[];
  ratingMeanings: string[];
  approvalPercentage: number;
  productionPercentage: number;
}

export interface AnsweredGate {
  id: string;
  label: string;
  result: ReviewResult;
  evidence: string;
}

export interface RatedCategory {
  id: string;
  label: string;
  score: number;
  maximum: number;
  minimumRequired: number | null;
  notes: string;
}

export interface ReviewEvaluation {
  hardGatePassed: boolean;
  failedHardGates: AnsweredGate[];
  untestedHardGates: AnsweredGate[];
  totalScore: number;
  maximumScore: number;
  percentage: number;
  failedCategoryMinimums: RatedCategory[];
  unratedCategories: string[];
  eligibleForDesignApproval: boolean;
  eligibleForProductionApproval: boolean;
  band: string;
  bandLabel: string;
  blockers: string[];
}

export interface ReviewView {
  attempt_id: string;
  reviewer: string;
  gates: AnsweredGate[];
  categories: RatedCategory[];
  rationale: string;
  decision: string;
  // Whatever the measurement found. Shape varies with what could be measured,
  // so it is read defensively wherever it is shown.
  measurements: Record<string, unknown>;
  evaluation: ReviewEvaluation;
  frozen: boolean;
  /** Gate ids the brief answers. Shown with their evidence, never offered as a
   * choice: a person ticking "product and blank defined" when no blank is
   * recorded is the assertion the scorecard exists to prevent. */
  derived_gates: string[];
  next_action: string;
}

export interface GateAnswer {
  id: string;
  result: ReviewResult;
  evidence?: string;
}

export interface CategoryAnswer {
  id: string;
  // The 0-5 rating the scorecard states. The server does the one conversion to
  // points, so a rating typed here and a rating measured off an image land on
  // the same scale.
  rating: number;
  notes?: string;
}

export interface Zone {
  key: string;
  width_mm: number;
  height_mm: number;
}

export async function fetchRubric(): Promise<Rubric> {
  return await json<Rubric>("/api/concepts/rubric");
}

export async function fetchReview(attemptId: string): Promise<ReviewView> {
  return await json<ReviewView>(`/api/concepts/attempts/${encodeURIComponent(attemptId)}/review`);
}

export async function saveReview(
  attemptId: string,
  reviewer: string,
  gates: GateAnswer[],
  categories: CategoryAnswer[],
  rationale = "",
): Promise<ReviewView> {
  return await json<ReviewView>(`/api/concepts/attempts/${encodeURIComponent(attemptId)}/review`, {
    method: "PUT",
    body: JSON.stringify({ reviewer, gates, categories, rationale }),
  });
}

export async function measureAttempt(attemptId: string): Promise<ReviewView> {
  return await json<ReviewView>(`/api/concepts/attempts/${encodeURIComponent(attemptId)}/measure`, {
    method: "POST",
    body: "{}",
  });
}

export async function fetchGarments(): Promise<Record<string, Zone[]>> {
  return await json<Record<string, Zone[]>>("/api/concepts/garments");
}

export interface PrintSpec {
  garment_key: string;
  zone_key: string;
  print_width_mm: number;
  garment_colour?: string;
}

export async function approveDesignWithSpec(
  attemptId: string,
  approvedBy: string,
  spec: PrintSpec,
): Promise<ApprovedDesignView> {
  return await json<ApprovedDesignView>(
    `/api/concepts/attempts/${encodeURIComponent(attemptId)}/approve-design`,
    { method: "POST", body: JSON.stringify({ approved_by: approvedBy, ...spec }) },
  );
}

export function printedVersionUrl(versionId: string, showZones = false): string {
  const suffix = showZones ? "?show_zones=true" : "";
  return `/api/concepts/versions/${encodeURIComponent(versionId)}/print.svg${suffix}`;
}

/* --- The work queue --------------------------------------------------------
 *
 * One row per thing being made, each carrying the one thing to do to it next.
 * Derived on the server from concepts, attempts, reviews and versions, so this
 * cannot disagree with the screens it sends you to.
 */

/** The stages the server sends today.
 *
 * `(string & {})` keeps the known names autocompleting while admitting one the
 * server adds before this file is redeployed. The union used to be closed, and
 * a closed union told the compiler a lookup was total when it was not -- which
 * is how `needs_brief` blanked the whole application. Types describe what the
 * API actually returns, not what it returned when they were written. */
export type WorkStage =
  | "awaiting_decision"
  | "review_open"
  | "needs_artwork"
  | "needs_brief"
  | "approved_unversioned"
  | "ready_to_print"
  | "unstarted"
  | "settled"
  | (string & Record<never, never>);

export interface WorkItem {
  concept_id: string;
  library: string;
  external_number: number;
  title: string;
  concept_status: string;
  research_run_id: string;
  research_concept_number: number | null;
  attempt_id: string | null;
  attempt_number: number | null;
  attempt_state: DesignAttemptState | null;
  has_artwork: boolean;
  percentage: number | null;
  eligible: boolean;
  blockers: string[];
  approved_version: number | null;
  approved_design_id: string | null;
  stage: WorkStage;
  next_action: string;
}

export async function fetchWork(includeSettled = false): Promise<WorkItem[]> {
  const suffix = includeSettled ? "?include_settled=true" : "";
  return await json<WorkItem[]>(`/api/concepts/work${suffix}`);
}

/* --- The brief: the constitution's steps 1-4 and 6 ------------------------- */

export interface BriefView {
  concept_id: string;
  garment_category: string;
  canonical_blank: string;
  fit_block: string;
  fabric_weight: string;
  garment_colour: string;
  wash: string;
  production_method: string;
  intended_use: string;
  commercial_tier: string;
  target_release: string;
  collection_role: string | null;
  graphic_archetype: string | null;
  layout_archetype: string | null;
  archetype_departure_reason: string;
  zones: Record<string, string>;
  typography: Record<string, string>;
  advisor_snapshot: Record<string, unknown>;
  notes: string;
  ready_for_artwork: boolean;
  next_action: string;
}

export async function fetchBrief(conceptId: string): Promise<BriefView> {
  return await json<BriefView>(`/api/concepts/${encodeURIComponent(conceptId)}/brief`);
}

export async function saveBrief(conceptId: string, brief: Partial<BriefView>): Promise<BriefView> {
  return await json<BriefView>(`/api/concepts/${encodeURIComponent(conceptId)}/brief`, {
    method: "PUT",
    body: JSON.stringify(brief),
  });
}

export interface AdvisorRecommendation {
  field: string;
  value: string;
  evidence: string;
  confidence: string;
}

export interface AdvisorDirection {
  input: string;
  intent: string;
  tradition: string;
  recommendations: AdvisorRecommendation[];
  alternatives: string[];
  not_decided: string[];
  generation_prompt: string;
  concept_id: string | null;
}

/** The advisor answers constitution steps 3 and 4 from 12,151 measured images.
 * Until Phase 4 nothing called it. */
export async function fetchAdvice(
  phrase: string,
  hasGraphic: boolean,
  tradition = "novelty",
): Promise<AdvisorDirection> {
  return await json<AdvisorDirection>("/api/design/advise", {
    method: "POST",
    body: JSON.stringify({ phrase, has_graphic: hasGraphic, tradition }),
  });
}

/** A batch-written concept picked at random for this tradition -- see
 * app/db/concept_pool_models.py. Written once ahead of time, not a live
 * model call; hit and miss by nature, same as the batch itself. */
export async function fetchRandomConcept(tradition: string): Promise<AdvisorDirection> {
  return await json<AdvisorDirection>("/api/design/random", {
    method: "POST",
    body: JSON.stringify({ tradition }),
  });
}

/** Takes one batch-written concept out of rotation. The only pruning tool
 * for the pool that doesn't require database access. */
export async function retireConcept(conceptId: string): Promise<void> {
  await json<{ concept_id: string; active: boolean }>(
    `/api/design/concept-pool/${encodeURIComponent(conceptId)}/retire`,
    { method: "POST" },
  );
}

/** Everything that leaves the building with one attempt: the words, the product
 * definition, the prompt and the evidence images. Composed on the server so the
 * text a person takes and the record of what they took cannot differ. */
export interface EvidenceImage {
  url: string;
  listing_id: string;
  filename: string;
}

export interface BriefPackage {
  text: string;
  evidence_images: EvidenceImage[];
  evidence_listing_ids: string[];
  research_run_id: string;
  evidence_count: number;
}

export async function fetchBriefPackage(attemptId: string): Promise<BriefPackage> {
  return await json<BriefPackage>(
    `/api/concepts/attempts/${encodeURIComponent(attemptId)}/brief-package`,
  );
}

export async function recordBriefTaken(attemptId: string): Promise<unknown> {
  return await json<unknown>(
    `/api/concepts/attempts/${encodeURIComponent(attemptId)}/brief-taken`,
    { method: "POST", body: "{}" },
  );
}

/* --- Gallery: every concept that was actually rendered and looked at ------
 *
 * Distinct from the concept pool (ideas) and from /advise (one prompt for one
 * typed idea) -- this is the durable record of a batch's real output: the
 * image and the exact prompt that produced it, kept whether or not the
 * concept survived review. See app/db/generation_sample_models.py.
 */

export type GenerationStatus = "kept" | "dropped";

export interface GenerationSample {
  id: string;
  tradition: string;
  concept_text: string;
  prompt: string;
  status: GenerationStatus;
  drop_reason: string | null;
  batch: string;
  created_at: string;
}

export interface GenerationSamplePage {
  items: GenerationSample[];
  total: number;
  page: number;
  page_size: number;
}

export async function fetchGenerations(
  page: number,
  pageSize = 16,
  tradition?: string,
  status?: GenerationStatus,
): Promise<GenerationSamplePage> {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  if (tradition) params.set("tradition", tradition);
  if (status) params.set("status_filter", status);
  return await json<GenerationSamplePage>(`/api/design/generations?${params.toString()}`);
}

export function generationImageUrl(sampleId: string, variant: "thumb" | "full" = "thumb"): string {
  return `/api/design/generations/${encodeURIComponent(sampleId)}/image?variant=${variant}`;
}

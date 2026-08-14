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

export type WorkStage =
  | "awaiting_decision"
  | "review_open"
  | "needs_artwork"
  | "approved_unversioned"
  | "ready_to_print"
  | "unstarted"
  | "settled";

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

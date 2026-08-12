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

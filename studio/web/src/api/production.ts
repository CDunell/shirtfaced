/**
 * Scene masters, coverage frames and scouted locations.
 *
 * The two decisions that gate a paid run live here: which image is a scene's
 * master, and which coverage frames Veo may animate. Both were command-line
 * only until this existed.
 */

import { ApiError } from "./client";

export interface AssetBrief {
  id: string;
  sha256: string;
  width: number;
  height: number;
  mime_type: string;
  status: string;
  rights_status: string;
}

export interface PanelPlanEntry {
  panel: number;
  title: string;
  summary: string;
}

export interface ContactSheet {
  id: string;
  label: string;
  status: string;
  rows: number;
  columns: number;
  panels: number;
  prompt_template: string | null;
  /** The numbered observations the coverage prompt asked for, in its order. */
  panel_plan: PanelPlanEntry[];
  approved_at: string | null;
  asset: AssetBrief;
  reference_asset_ids: string[];
}

export interface CoverageFrame {
  id: string;
  name: string;
  /** A crop carries a box; a Nano extraction carries a panel and no box. */
  x: number | null;
  y: number | null;
  width: number | null;
  height: number | null;
  panel: number | null;
  operation: string;
  approved_for_veo: boolean;
  frame_sha256: string;
  source_master_sha256: string;
  /** Cut from a master that is no longer approved. Needs re-cutting. */
  stale: boolean;
  asset: AssetBrief;
}

export interface SceneMaster {
  id: string;
  scene_key: string;
  status: string;
  approved_at: string | null;
  notes: string | null;
  asset: AssetBrief;
  coverage: CoverageFrame[];
  contact_sheets: ContactSheet[];
}

export interface Scene {
  scene_key: string;
  approved_master_id: string | null;
  masters: SceneMaster[];
}

export interface LocationPlate {
  id: string;
  role: string;
  sort_order: number;
  is_base_master: boolean;
  camera_position: string | null;
  notes: string | null;
  asset: AssetBrief;
  /** Why this plate cannot be a base master. Empty when it can. */
  blocking: string[];
  ratio: number;
  lateral_room_px: number;
  meets_wide_preference: boolean;
}

export interface ScoutLocation {
  id: string;
  slug: string;
  display_name: string;
  parent_slug: string | null;
  location_type: string | null;
  description: string | null;
  status: string;
  assets: LocationPlate[];
}

/** Bytes of any library asset, addressed by identifier. Immutable, so cacheable. */
export function previewSource(asset: AssetBrief): string {
  return `/api/visual-assets/${asset.id}/preview`;
}

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

async function send<T>(
  path: string,
  method: string,
  body?: unknown,
  signal?: AbortSignal,
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
  if (!response.ok) throw await failure(response);
  if (response.status === 204) return null as T;
  return (await response.json()) as T;
}

async function upload<T>(path: string, body: FormData): Promise<T> {
  const response = await fetch(path, { method: "POST", body });
  if (!response.ok) throw await failure(response);
  return (await response.json()) as T;
}

export function fetchScenes(signal?: AbortSignal): Promise<Scene[]> {
  return send<Scene[]>("/api/scenes", "GET", undefined, signal);
}

export function registerMaster(
  sceneKey: string,
  file: File,
  options: { approve?: boolean; notes?: string } = {},
): Promise<SceneMaster> {
  const body = new FormData();
  body.append("file", file);
  body.append("approve", String(options.approve ?? false));
  if (options.notes) body.append("notes", options.notes);
  return upload<SceneMaster>(`/api/scenes/${sceneKey}/masters`, body);
}

export function approveMaster(masterId: string, note?: string): Promise<SceneMaster> {
  return send<SceneMaster>(`/api/scene-masters/${masterId}/approve`, "POST", {
    note: note ?? null,
  });
}

export function cutCoverage(
  sceneKey: string,
  frame: { name: string; x: number; y?: number; height?: number },
): Promise<CoverageFrame> {
  return send<CoverageFrame>(`/api/scenes/${sceneKey}/coverage`, "POST", frame);
}

export function approveCoverage(frameId: string, note?: string): Promise<CoverageFrame> {
  return send<CoverageFrame>(`/api/coverage/${frameId}/approve`, "POST", { note: note ?? null });
}

export function registerContactSheet(
  sceneKey: string,
  file: File,
  options: {
    label: string;
    rows?: number;
    columns?: number;
    referenceAssetIds?: string[];
    promptTemplate?: string;
    approve?: boolean;
  },
): Promise<ContactSheet> {
  const body = new FormData();
  body.append("file", file);
  body.append("label", options.label);
  body.append("rows", String(options.rows ?? 3));
  body.append("columns", String(options.columns ?? 3));
  if (options.promptTemplate) body.append("prompt_template", options.promptTemplate);
  if (options.referenceAssetIds?.length) {
    body.append("reference_asset_ids", options.referenceAssetIds.join(","));
  }
  body.append("approve", String(options.approve ?? false));
  return upload<ContactSheet>(`/api/scenes/${sceneKey}/contact-sheets`, body);
}

/** Says no on the sheet, not only on its bytes. Nothing is deleted. */
export function rejectContactSheet(sheetId: string, note?: string): Promise<ContactSheet> {
  return send<ContactSheet>(`/api/contact-sheets/${sheetId}/reject`, "POST", {
    note: note ?? null,
  });
}

export function approveContactSheet(sheetId: string, note?: string): Promise<ContactSheet> {
  return send<ContactSheet>(`/api/contact-sheets/${sheetId}/approve`, "POST", {
    note: note ?? null,
  });
}

export function recordPanel(
  sceneKey: string,
  file: File,
  options: { name: string; panel: number; aspectRatio?: string; model?: string },
): Promise<CoverageFrame> {
  const body = new FormData();
  body.append("file", file);
  body.append("name", options.name);
  body.append("panel", String(options.panel));
  body.append("aspect_ratio", options.aspectRatio ?? "9:16");
  if (options.model) body.append("model", options.model);
  return upload<CoverageFrame>(`/api/scenes/${sceneKey}/panels`, body);
}

export interface ReferenceChoice {
  key: string;
  slug: string;
  role: string;
}

export interface PromptChoice {
  name: string;
  characters: number;
}

export interface PipelineInputs {
  scene_key: string;
  /** The scene's own persisted coverage prompt, if its key matches a filename. */
  prompt: string | null;
  source: string | null;
  available_prompts: PromptChoice[];
  /** The scene's shared motion direction, read from its shot specification. */
  motion_prompt: string | null;
  references: ReferenceChoice[];
  attempts: number;
  media_live: boolean;
}

export function fetchPipelineInputs(
  sceneKey: string,
  signal?: AbortSignal,
): Promise<PipelineInputs> {
  return send<PipelineInputs>(`/api/scenes/${sceneKey}/pipeline`, "GET", undefined, signal);
}

/** Sends master + chosen references to Nano and stores the sheet it returns. */
export function generateSheet(
  sceneKey: string,
  input: { label: string; selections: string[]; prompt?: string; prompt_name?: string },
): Promise<ContactSheet> {
  return send<ContactSheet>(`/api/scenes/${sceneKey}/generate-sheet`, "POST", input);
}

/** Sends the approved sheet back to Nano for one panel. */
export function extractPanel(
  sceneKey: string,
  input: { panel: number; name: string; selections: string[] },
): Promise<CoverageFrame> {
  return send<CoverageFrame>(`/api/scenes/${sceneKey}/extract-panel`, "POST", input);
}

export interface VideoBrief {
  id: string;
  sha256: string;
  status: string;
  duration_ms: number | null;
  width: number | null;
  height: number | null;
  frame_rate: number | null;
  has_audio: boolean | null;
  byte_size: number;
}

export interface MotionTake {
  id: string;
  shot: string;
  coverage_frame_id: string;
  attempt: number;
  status: string;
  keeper_from_ms: number | null;
  keeper_to_ms: number | null;
  notes: string | null;
  first_frame_sha256: string;
  /** The shot has been re-extracted since this was animated. */
  stale: boolean;
  video: VideoBrief;
}

export function fetchTakes(sceneKey: string, signal?: AbortSignal): Promise<MotionTake[]> {
  return send<MotionTake[]>(`/api/scenes/${sceneKey}/takes`, "GET", undefined, signal);
}

/** Animates an approved shot. The seed is resolved from the scene, not named. */
export function generateTake(
  sceneKey: string,
  input: { name: string; prompt?: string; aspect_ratio?: string },
): Promise<MotionTake> {
  return send<MotionTake>(`/api/scenes/${sceneKey}/generate-take`, "POST", input);
}

/** One keeper per shot. Naming a new one stands the previous one down. */
export function keepTake(
  takeId: string,
  input: { keeper_from_ms?: number | null; keeper_to_ms?: number | null; note?: string | null },
): Promise<MotionTake> {
  return send<MotionTake>(`/api/takes/${takeId}/keep`, "POST", input);
}

export function rejectMotionTake(takeId: string, note?: string): Promise<MotionTake> {
  return send<MotionTake>(`/api/takes/${takeId}/reject`, "POST", { note: note ?? null });
}

/** The clip's own bytes, for a <video> element. */
export function takeVideoSource(takeId: string): string {
  return `/api/takes/${takeId}/video`;
}

export interface VeoTrigger {
  /** Where the file goes, repository-relative. */
  path: string;
  content: string;
  /** GitHub's new-file editor, pre-filled. The operator presses Commit. */
  commit_url: string;
}

/** The trigger file that animates an approved shot, built server-side. */
export function fetchVeoTrigger(frameId: string): Promise<VeoTrigger> {
  return send<VeoTrigger>(`/api/coverage/${frameId}/veo-trigger`, "GET");
}

export function rejectTake(assetId: string, note?: string): Promise<AssetBrief> {
  return send<AssetBrief>(`/api/visual-assets/${assetId}/reject`, "POST", { note: note ?? null });
}

export function fetchLocations(signal?: AbortSignal): Promise<ScoutLocation[]> {
  return send<ScoutLocation[]>("/api/locations", "GET", undefined, signal);
}

export function fetchLocationRoles(signal?: AbortSignal): Promise<string[]> {
  return send<string[]>("/api/locations/roles", "GET", undefined, signal);
}

export function createLocation(input: {
  slug: string;
  display_name: string;
  parent_slug?: string | null;
}): Promise<ScoutLocation> {
  return send<ScoutLocation>("/api/locations", "POST", input);
}

export function addPlate(
  slug: string,
  file: File,
  options: { role: string; cameraPosition?: string; promote?: boolean },
): Promise<LocationPlate> {
  const body = new FormData();
  body.append("file", file);
  body.append("role", options.role);
  if (options.cameraPosition) body.append("camera_position", options.cameraPosition);
  body.append("promote", String(options.promote ?? false));
  return upload<LocationPlate>(`/api/locations/${slug}/plates`, body);
}

export function promotePlate(linkId: string, note?: string): Promise<LocationPlate> {
  return send<LocationPlate>(`/api/location-plates/${linkId}/promote`, "POST", {
    note: note ?? null,
  });
}

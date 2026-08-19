import { ApiError } from "./client";

export interface DirectAsset {
  id: string;
  sha256: string;
  width: number;
  height: number;
  mime_type: string;
  status: string;
}

export interface SceneShotMaster {
  id: string;
  scene_key: string;
  name: string;
  status: string;
  sort_order: number;
  notes: string | null;
  approved_at: string | null;
  asset: DirectAsset;
}

export interface SceneShotMasters {
  scene_key: string;
  approved_count: number;
  maximum_approved: number;
  shot_masters: SceneShotMaster[];
}

export interface SceneShotTake {
  stamp: string;
  duration_seconds: number | null;
  width: number | null;
  height: number | null;
  silent: boolean;
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

async function send<T>(path: string, method = "GET"): Promise<T> {
  const response = await fetch(path, { method, headers: { Accept: "application/json" } });
  if (!response.ok) throw await failure(response);
  return (await response.json()) as T;
}

async function upload<T>(path: string, body: FormData): Promise<T> {
  const response = await fetch(path, { method: "POST", body });
  if (!response.ok) throw await failure(response);
  return (await response.json()) as T;
}

export function fetchShotMasterScenes(): Promise<string[]> {
  return send<string[]>("/api/shot-master-scenes");
}

export function fetchSceneShotMasters(sceneKey: string): Promise<SceneShotMasters> {
  return send<SceneShotMasters>(`/api/scenes/${sceneKey}/shot-masters`);
}

export function registerSceneShotMaster(
  sceneKey: string,
  file: File,
  name: string,
  notes?: string,
): Promise<SceneShotMaster> {
  const body = new FormData();
  body.append("file", file);
  body.append("name", name);
  if (notes) body.append("notes", notes);
  return upload<SceneShotMaster>(`/api/scenes/${sceneKey}/shot-masters`, body);
}

export function approveSceneShotMaster(shotId: string): Promise<SceneShotMasters> {
  return send<SceneShotMasters>(`/api/shot-masters/${shotId}/approve`, "POST");
}

export function rejectSceneShotMaster(shotId: string): Promise<SceneShotMasters> {
  return send<SceneShotMasters>(`/api/shot-masters/${shotId}/reject`, "POST");
}

export function animateSceneShotMaster(shotId: string): Promise<SceneShotTake> {
  return send<SceneShotTake>(`/api/shot-masters/${shotId}/animate`, "POST");
}

export function fetchSceneShotTakes(shotId: string): Promise<SceneShotTake[]> {
  return send<SceneShotTake[]>(`/api/shot-masters/${shotId}/takes`);
}

export function sceneShotPreview(assetId: string): string {
  return `/api/visual-assets/${assetId}/preview`;
}

export function sceneShotTakeSource(shotId: string, stamp?: string): string {
  const suffix = stamp ? `?v=${encodeURIComponent(stamp)}` : "";
  return `/api/shot-masters/${shotId}/take${suffix}`;
}

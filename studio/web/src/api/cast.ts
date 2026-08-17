/**
 * The cast library.
 *
 * Every reference is a database row with an identity, so a member can have two
 * photographs or twenty and nothing here changes shape. Bytes come from
 * `/api/visual-assets/{id}/bytes`, addressed by identifier — the browser never
 * names a file path.
 */

import { ApiError } from "./client";

export type VisualAssetStatus = "pending" | "approved" | "deprecated" | "rejected";
export type RightsStatus = "verified" | "unverified" | "refused";

export interface VisualAsset {
  id: string;
  kind: string;
  role: string | null;
  sha256: string;
  mime_type: string;
  width: number;
  height: number;
  byte_size: number;
  aspect_ratio: number;
  source_type: string;
  status: VisualAssetStatus;
  rights_status: RightsStatus;
  description: string | null;
  approved_by: string | null;
}

export interface CastAsset {
  link_id: string;
  role: string;
  sort_order: number;
  is_primary: boolean;
  notes: string | null;
  asset: VisualAsset;
  /** Set when the upload turned out to be bytes the library already held. */
  duplicate_of?: string | null;
}

export interface CastMember {
  id: string;
  slug: string;
  display_name: string;
  description: string | null;
  status: string;
  canonical_metadata: Record<string, unknown>;
  assets: CastAsset[];
}

/** Where an asset's bytes are served from. Immutable, so it caches forever. */
export function assetSource(asset: VisualAsset): string {
  return `/api/visual-assets/${asset.id}/bytes`;
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

export function fetchCast(signal?: AbortSignal): Promise<CastMember[]> {
  return send<CastMember[]>("/api/cast", "GET", undefined, signal);
}

export function fetchCastRoles(signal?: AbortSignal): Promise<string[]> {
  return send<string[]>("/api/cast/roles", "GET", undefined, signal);
}

/** A person, before any photograph of them exists. */
export function createCastMember(slug: string, displayName: string): Promise<CastMember> {
  return send<CastMember>("/api/cast", "POST", {
    slug,
    display_name: displayName,
    canonical_metadata: {},
  });
}

/** The slug the API will accept: lowercase, digits, single hyphens. */
export function slugify(name: string): string {
  return name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export interface UploadOptions {
  role: string;
  description?: string;
  isPrimary?: boolean;
  approve?: boolean;
}

/** Add a reference. The third photograph is the same call as the first. */
export async function uploadCastAsset(
  slug: string,
  file: File,
  options: UploadOptions,
): Promise<CastAsset> {
  const body = new FormData();
  body.append("file", file);
  body.append("role", options.role);
  if (options.description) body.append("description", options.description);
  body.append("is_primary", String(options.isPrimary ?? false));
  body.append("approve", String(options.approve ?? false));

  const response = await fetch(`/api/cast/${slug}/assets`, { method: "POST", body });
  if (!response.ok) throw await failure(response);
  return (await response.json()) as CastAsset;
}

export function updateCastAsset(
  slug: string,
  linkId: string,
  changes: { role?: string; sort_order?: number; is_primary?: boolean; notes?: string },
): Promise<CastAsset> {
  return send<CastAsset>(`/api/cast/${slug}/assets/${linkId}`, "PATCH", changes);
}

/** Detach, not destroy: the asset keeps its identity and its history. */
export async function detachCastAsset(slug: string, linkId: string): Promise<void> {
  await send<null>(`/api/cast/${slug}/assets/${linkId}`, "DELETE");
}

export function approveAsset(assetId: string, note?: string): Promise<VisualAsset> {
  return send<VisualAsset>(`/api/visual-assets/${assetId}/approve`, "POST", { note: note ?? null });
}

export function deprecateAsset(assetId: string, note?: string): Promise<VisualAsset> {
  return send<VisualAsset>(`/api/visual-assets/${assetId}/deprecate`, "POST", {
    note: note ?? null,
  });
}

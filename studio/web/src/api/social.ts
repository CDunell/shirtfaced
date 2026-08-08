import { ApiError } from "./client";

export type SocialPostState = "review_required" | "approved" | "rejected" | "queued" | "live";
export type SocialDerivativeReviewState = "review_required" | "approved" | "rejected";
export type PublicationState =
  "queued" | "scheduled" | "held" | "publishing" | "published" | "failed" | "cancelled";

export interface SocialDerivative {
  id: string;
  output_key: string;
  channel: string;
  width: number;
  height: number;
  filename: string;
  sha256: string;
  byte_size: number;
  url: string;
  review_state: SocialDerivativeReviewState;
  rejection_reason: string | null;
  reviewed_at: string | null;
}

export interface PublicationJob {
  id: string;
  social_post_id: string;
  derivative_id: string;
  channel: string;
  output_key: string;
  filename: string;
  derivative_url: string;
  source_label: string;
  caption: string;
  campaign_id: string | null;
  state: PublicationState;
  scheduled_at: string | null;
  scheduled_timezone: string;
  recommended_at: string | null;
  locked: boolean;
  external_post_id: string | null;
  published_at: string | null;
  failure_reason: string | null;
  retry_count: number;
  max_attempts: number;
  next_attempt_at: string | null;
  last_attempt_at: string | null;
  adapter: string | null;
  publish_receipt: Record<string, unknown> | null;
}

export interface SocialPost {
  id: string;
  source_photo_id: string;
  source_label: string;
  theme: string;
  branding: string;
  caption: string;
  campaign_id: string | null;
  state: SocialPostState;
  approved_at: string | null;
  rejected_at: string | null;
  created_at: string;
  derivatives: SocialDerivative[];
  jobs: PublicationJob[];
}

export interface LocalSocialDerivative {
  output_key: string;
  width: number;
  height: number;
  filename: string;
  blob: Blob;
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

export async function saveSocialPost(input: {
  sourcePhotoId: string;
  theme: string;
  branding: string;
  caption: string;
  derivatives: LocalSocialDerivative[];
}): Promise<SocialPost> {
  const body = new FormData();
  body.append("source_photo_id", input.sourcePhotoId);
  body.append("theme", input.theme);
  body.append("branding", input.branding);
  body.append("caption", input.caption);
  body.append(
    "derivative_metadata",
    JSON.stringify(
      input.derivatives.map(({ output_key, width, height, filename }) => ({
        output_key,
        width,
        height,
        filename,
      })),
    ),
  );
  for (const derivative of input.derivatives)
    body.append("files", derivative.blob, derivative.filename);
  return await json<SocialPost>("/api/social/posts", { method: "POST", body });
}

export async function fetchSocialPosts(state?: SocialPostState): Promise<SocialPost[]> {
  const suffix = state ? `?state=${encodeURIComponent(state)}` : "";
  return await json<SocialPost[]>(`/api/social/posts${suffix}`);
}

export async function approveSocialPost(id: string): Promise<SocialPost> {
  return await json<SocialPost>(`/api/social/posts/${encodeURIComponent(id)}/approve`, {
    method: "POST",
    body: "{}",
  });
}

export async function rejectSocialPost(id: string, reason = ""): Promise<SocialPost> {
  return await json<SocialPost>(`/api/social/posts/${encodeURIComponent(id)}/reject`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}

export async function approveSocialDerivative(id: string): Promise<SocialPost> {
  return await json<SocialPost>(`/api/social/derivatives/${encodeURIComponent(id)}/approve`, {
    method: "POST",
    body: "{}",
  });
}

export async function rejectSocialDerivative(id: string, reason = ""): Promise<SocialPost> {
  return await json<SocialPost>(`/api/social/derivatives/${encodeURIComponent(id)}/reject`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}

export async function queueSocialPost(
  id: string,
  scheduledAt?: string,
  timezone = "Australia/Brisbane",
): Promise<PublicationJob[]> {
  return await json<PublicationJob[]>(`/api/social/posts/${encodeURIComponent(id)}/queue`, {
    method: "POST",
    body: JSON.stringify({ scheduled_at: scheduledAt ?? null, timezone }),
  });
}

export async function fetchSocialQueue(): Promise<PublicationJob[]> {
  return await json<PublicationJob[]>("/api/social/queue");
}

export async function fetchSocialLive(): Promise<PublicationJob[]> {
  return await json<PublicationJob[]>("/api/social/live");
}

export async function scheduleSocialJob(
  id: string,
  scheduledAt: string,
  timezone = "Australia/Brisbane",
): Promise<PublicationJob> {
  return await json<PublicationJob>(`/api/social/jobs/${encodeURIComponent(id)}/schedule`, {
    method: "POST",
    body: JSON.stringify({ scheduled_at: scheduledAt, timezone }),
  });
}

export async function holdSocialJob(id: string): Promise<PublicationJob> {
  return await json<PublicationJob>(`/api/social/jobs/${encodeURIComponent(id)}/hold`, {
    method: "POST",
    body: "{}",
  });
}

export async function cancelSocialJob(id: string): Promise<PublicationJob> {
  return await json<PublicationJob>(`/api/social/jobs/${encodeURIComponent(id)}/cancel`, {
    method: "POST",
    body: "{}",
  });
}

export async function publishSocialJobNow(id: string): Promise<PublicationJob> {
  return await json<PublicationJob>(`/api/social/jobs/${encodeURIComponent(id)}/publish-now`, {
    method: "POST",
    body: "{}",
  });
}

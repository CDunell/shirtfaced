/* eslint-disable @typescript-eslint/no-confusing-void-expression */
/** Social Studio: create → review → queue → live. */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Button,
  Card,
  Checkbox,
  FormControl,
  HeadingSmall,
  LabelSmall,
  Notification,
  ParagraphSmall,
  ParagraphXSmall,
  Select,
  Tag,
} from "./ui";

import { PageTitle } from "./chrome";

import { ApiError, fetchPhotos, uploadPhoto, type Photo } from "../api/client";
import { loadCanvasImage } from "../lib/loadCanvasImage";
import {
  approveSocialDerivative,
  approveSocialPost,
  cancelSocialJob,
  fetchSocialLive,
  fetchSocialPosts,
  fetchSocialQueue,
  holdSocialJob,
  publishSocialJobNow,
  queueSocialPost,
  rejectSocialDerivative,
  rejectSocialPost,
  saveSocialPost,
  scheduleSocialJob,
  type PublicationJob,
  type SocialPost,
} from "../api/social";

type SocialTheme = "auto" | "light" | "dark" | "adaptive";
type ResolvedTheme = Exclude<SocialTheme, "auto">;
type Branding = "clean" | "fingerprint" | "identity";
type OutputKey = "instagram_feed" | "instagram_story" | "reel_cover" | "tiktok_cover";
type SocialView = "create" | "approval" | "queue" | "live";

interface OutputSpec {
  key: OutputKey;
  label: string;
  width: number;
  height: number;
  suffix: string;
}

interface ExportedFile extends OutputSpec {
  url: string;
  filename: string;
  theme: ResolvedTheme;
  blob: Blob;
}

const OUTPUTS: OutputSpec[] = [
  {
    key: "instagram_feed",
    label: "Instagram feed / carousel",
    width: 1080,
    height: 1350,
    suffix: "IG-FEED",
  },
  {
    key: "instagram_story",
    label: "Instagram Story",
    width: 1080,
    height: 1920,
    suffix: "IG-STORY",
  },
  { key: "reel_cover", label: "Reel cover", width: 1080, height: 1920, suffix: "REEL-COVER" },
  { key: "tiktok_cover", label: "TikTok cover", width: 1080, height: 1920, suffix: "TIKTOK-COVER" },
];

const THEME_OPTIONS = [
  { value: "auto", label: "Auto — choose from image" },
  { value: "light", label: "Light — ink marks" },
  { value: "dark", label: "Dark — paper marks" },
  { value: "adaptive", label: "Adaptive — backed mark" },
];

const BRANDING_OPTIONS = [
  { value: "clean", label: "Clean — no overlay" },
  { value: "fingerprint", label: "Fingerprint — minimal mark" },
  { value: "identity", label: "Identity — stronger Shirtfaced layer" },
];

function describe(cause: unknown): string {
  if (cause instanceof ApiError) return cause.message;
  return cause instanceof Error ? cause.message : String(cause);
}

function loadOverlayImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("A Shirtfaced overlay could not be loaded."));
    image.src = url;
  });
}

function cover(
  ctx: CanvasRenderingContext2D,
  image: HTMLImageElement,
  width: number,
  height: number,
): void {
  const scale = Math.max(width / image.naturalWidth, height / image.naturalHeight);
  const sourceWidth = width / scale;
  const sourceHeight = height / scale;
  const sx = (image.naturalWidth - sourceWidth) / 2;
  const sy = (image.naturalHeight - sourceHeight) / 2;
  ctx.drawImage(image, sx, sy, sourceWidth, sourceHeight, 0, 0, width, height);
}

function analyseTheme(image: HTMLImageElement): ResolvedTheme {
  const canvas = document.createElement("canvas");
  canvas.width = 64;
  canvas.height = 64;
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  if (!ctx) return "adaptive";
  cover(ctx, image, 64, 64);
  const data = ctx.getImageData(0, 0, 64, 64).data;
  const values: number[] = [];
  for (let i = 0; i < data.length; i += 16) {
    values.push(
      0.2126 * (data[i] ?? 0) + 0.7152 * (data[i + 1] ?? 0) + 0.0722 * (data[i + 2] ?? 0),
    );
  }
  const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
  const variance = values.reduce((sum, value) => sum + (value - mean) ** 2, 0) / values.length;
  if (Math.sqrt(variance) > 58 && mean > 65 && mean < 205) return "adaptive";
  return mean >= 145 ? "light" : "dark";
}

function overlayPath(theme: ResolvedTheme, branding: Branding, output: OutputKey): string | null {
  if (branding === "clean") return null;
  if (output === "instagram_feed") {
    if (branding === "fingerprint") return `/social-assets/v3/${theme}-corner-mark-4x5.svg`;
    return theme === "adaptive"
      ? "/social-assets/v3/adaptive-feed-badge-4x5.svg"
      : `/social-assets/v3/${theme}-feed-4x5.svg`;
  }
  if (theme === "adaptive") return "/social-assets/v3/adaptive-reel-badge-9x16.svg";
  return branding === "fingerprint"
    ? `/social-assets/v3/${theme}-title-bug-9x16.svg`
    : `/social-assets/v3/${theme}-reel-9x16.svg`;
}

function blobFromCanvas(canvas: HTMLCanvasElement): Promise<Blob> {
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) =>
        blob ? resolve(blob) : reject(new Error("The browser could not encode the export.")),
      "image/jpeg",
      0.94,
    );
  });
}

function cleanName(label: string): string {
  return (
    label
      .toUpperCase()
      .replace(/[^A-Z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 54) || "ASSET"
  );
}

function releaseExports(files: ExportedFile[]): void {
  files.forEach((item) => URL.revokeObjectURL(item.url));
}

function localDate(value: string | null): string {
  if (!value) return "Unscheduled";
  return new Date(value).toLocaleString();
}

function reviewTag(state: string): React.JSX.Element {
  return (
    <Tag kind={state === "approved" ? "positive" : "neutral"}>{state.replace("_", " ")}</Tag>
  );
}

export function SocialBench(): React.JSX.Element {
  const [view, setView] = useState<SocialView>("create");
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [photoValue, setPhotoValue] = useState<string>("");
  const [themeValue, setThemeValue] = useState<string>("auto");
  const [brandingValue, setBrandingValue] = useState<string>("fingerprint");
  const [selectedOutputs, setSelectedOutputs] = useState<Set<OutputKey>>(
    new Set(OUTPUTS.map((item) => item.key)),
  );
  const [resolvedTheme, setResolvedTheme] = useState<ResolvedTheme | null>(null);
  const [exports, setExports] = useState<ExportedFile[]>([]);
  const [caption, setCaption] = useState("");
  const [approval, setApproval] = useState<SocialPost[]>([]);
  const [queue, setQueue] = useState<PublicationJob[]>([]);
  const [live, setLive] = useState<PublicationJob[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedId, setSavedId] = useState<string | null>(null);
  const uploadInput = useRef<HTMLInputElement | null>(null);

  const photo = useMemo(
    () => photos.find((item) => item.id === photoValue) ?? null,
    [photos, photoValue],
  );

  const refreshPhotos = useCallback(async (): Promise<Photo[]> => {
    const found = await fetchPhotos();
    setPhotos(found);
    return found;
  }, []);

  const refreshPublishing = useCallback(async () => {
    const [posts, jobs, published] = await Promise.all([
      fetchSocialPosts(),
      fetchSocialQueue(),
      fetchSocialLive(),
    ]);
    setApproval(
      posts.filter((item) => item.state === "review_required" || item.state === "approved"),
    );
    setQueue(jobs);
    setLive(published);
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      void refreshPhotos()
        .then((found) => {
          const first = found[0];
          if (first) setPhotoValue(first.id);
        })
        .catch((cause: unknown) => setError(describe(cause)));
      void refreshPublishing().catch((cause: unknown) => setError(describe(cause)));
    }, 0);
    return () => clearTimeout(timer);
  }, [refreshPhotos, refreshPublishing]);

  const go = useCallback(async () => {
    if (!photo || selectedOutputs.size === 0) return;
    setBusy(true);
    setError(null);
    setSavedId(null);
    try {
      const source = await loadCanvasImage(photo.url);
      const requested = (themeValue || "auto") as SocialTheme;
      const chosenTheme: ResolvedTheme = requested === "auto" ? analyseTheme(source) : requested;
      const branding = (brandingValue || "fingerprint") as Branding;
      const made: ExportedFile[] = [];
      for (const spec of OUTPUTS.filter((item) => selectedOutputs.has(item.key))) {
        const canvas = document.createElement("canvas");
        canvas.width = spec.width;
        canvas.height = spec.height;
        const ctx = canvas.getContext("2d");
        if (!ctx) throw new Error("Canvas rendering is unavailable in this browser.");
        cover(ctx, source, spec.width, spec.height);
        const overlay = overlayPath(chosenTheme, branding, spec.key);
        if (overlay) ctx.drawImage(await loadOverlayImage(overlay), 0, 0, spec.width, spec.height);
        const blob = await blobFromCanvas(canvas);
        const filename = `SF_${cleanName(photo.label)}_${spec.suffix}.jpg`;
        made.push({ ...spec, blob, url: URL.createObjectURL(blob), filename, theme: chosenTheme });
      }
      setExports((old) => {
        releaseExports(old);
        return made;
      });
      setResolvedTheme(chosenTheme);
    } catch (cause) {
      setError(describe(cause));
    } finally {
      setBusy(false);
    }
  }, [brandingValue, photo, selectedOutputs, themeValue]);

  const saveForReview = useCallback(async () => {
    if (!photo || !resolvedTheme || exports.length === 0) return;
    setBusy(true);
    setError(null);
    try {
      const branding = brandingValue || "fingerprint";
      const saved = await saveSocialPost({
        sourcePhotoId: photo.id,
        theme: resolvedTheme,
        branding,
        caption,
        derivatives: exports.map((item) => ({
          output_key: item.key,
          width: item.width,
          height: item.height,
          filename: item.filename,
          blob: item.blob,
        })),
      });
      setSavedId(saved.id);
      await refreshPublishing();
      setView("approval");
    } catch (cause) {
      setError(describe(cause));
    } finally {
      setBusy(false);
    }
  }, [brandingValue, caption, exports, photo, refreshPublishing, resolvedTheme]);

  const act = useCallback(
    async (action: () => Promise<unknown>) => {
      setBusy(true);
      setError(null);
      try {
        await action();
        await refreshPublishing();
      } catch (cause) {
        setError(describe(cause));
      } finally {
        setBusy(false);
      }
    },
    [refreshPublishing],
  );

  const nav = (id: SocialView, label: string) => (
    <Button
      key={id}
      size="compact"
      variant={view === id ? "primary" : "secondary"}
      onClick={() => setView(id)}
    >
      {label}
    </Button>
  );

  return (
    <>
      <PageTitle>Social Studio</PageTitle>
      <div className="mb-[18px] flex flex-wrap gap-2">
        {nav("create", "Create")}
        {nav("approval", `Approval ${String(approval.length)}`)}
        {nav("queue", `Queue ${String(queue.length)}`)}
        {nav("live", `Live ${String(live.length)}`)}
      </div>
      {error ? <Notification kind="negative">{error}</Notification> : null}

      {view === "create" ? (
        <>
          <ParagraphSmall className="mt-0 text-ink/70">
            Pick the asset. Pick the outputs. GO makes the package; Save for review freezes the
            exact files.
          </ParagraphSmall>
          <div className="grid grid-cols-1 items-start gap-4 md:grid-cols-[minmax(280px,1.2fr)_minmax(260px,.8fr)]">
            <Card>
              <FormControl label="Source asset">
                <Select
                  options={photos.map((item) => ({ value: item.id, label: item.label }))}
                  value={photoValue}
                  onChange={(value) => {
                    setPhotoValue(value);
                    setSavedId(null);
                  }}
                />
              </FormControl>
              <Button
                size="compact"
                variant="secondary"
                disabled={busy}
                onClick={() => uploadInput.current?.click()}
              >
                Upload photo
              </Button>
              <input
                ref={uploadInput}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                hidden
                onChange={(event) => {
                  const file = event.currentTarget.files?.[0];
                  if (file)
                    void act(async () => {
                      const uploaded = await uploadPhoto(file);
                      await refreshPhotos();
                      setPhotoValue(uploaded.id);
                    });
                  event.currentTarget.value = "";
                }}
              />
              {photo ? (
                <img
                  src={photo.url}
                  alt="Selected source"
                  className="mt-3 aspect-[4/5] w-full rounded-2xl object-cover"
                />
              ) : null}
              {photo ? (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  <Tag kind="neutral">
                    {String(photo.width)}×{String(photo.height)}
                  </Tag>
                  <Tag kind="neutral">{photo.uploaded ? "uploaded" : "world asset"}</Tag>
                </div>
              ) : null}
            </Card>
            <Card>
              <FormControl label="Contrast treatment">
                <Select options={THEME_OPTIONS} value={themeValue} onChange={setThemeValue} />
              </FormControl>
              <FormControl label="Branding">
                <Select options={BRANDING_OPTIONS} value={brandingValue} onChange={setBrandingValue} />
              </FormControl>
              <LabelSmall>Outputs</LabelSmall>
              <div className="mt-2 mb-4">
                {OUTPUTS.map((spec) => (
                  <div key={spec.key}>
                    <Checkbox
                      checked={selectedOutputs.has(spec.key)}
                      onChange={() =>
                        setSelectedOutputs((old) => {
                          const next = new Set(old);
                          if (next.has(spec.key)) next.delete(spec.key);
                          else next.add(spec.key);
                          return next;
                        })
                      }
                    >
                      {spec.label}
                    </Checkbox>
                  </div>
                ))}
              </div>
              <FormControl
                label="Publishing caption"
                caption="Sent with the post. It is not burned into the image/video."
              >
                <textarea
                  value={caption}
                  onChange={(event) => setCaption(event.target.value)}
                  rows={4}
                  className="w-full rounded-lg border border-ink/15 bg-paper px-2.5 py-2.5 font-[inherit] text-ink"
                />
              </FormControl>
              <Button
                disabled={!photo || selectedOutputs.size === 0 || busy}
                onClick={() => void go()}
                className="w-full min-h-[52px] font-bold"
              >
                {busy ? "GO…" : "GO"}
              </Button>
            </Card>
          </div>
          {exports.length > 0 ? (
            <div className="mt-[22px]">
              <div className="flex flex-wrap items-center justify-between gap-2.5">
                <div>
                  <HeadingSmall className="mb-0">Ready</HeadingSmall>
                  <ParagraphXSmall className="mt-0">
                    {resolvedTheme ? `Resolved ${resolvedTheme}.` : ""}
                  </ParagraphXSmall>
                </div>
                <Button disabled={Boolean(savedId) || busy} onClick={() => void saveForReview()}>
                  {savedId ? "Saved for review" : busy ? "Saving…" : "Save for review"}
                </Button>
              </div>
              <div className="mt-2.5 grid grid-cols-[repeat(auto-fill,minmax(210px,1fr))] gap-3">
                {exports.map((item) => (
                  <Card key={item.key}>
                    <img
                      src={item.url}
                      alt={item.label}
                      className="w-full rounded-[10px] object-cover"
                      style={{ aspectRatio: `${String(item.width)} / ${String(item.height)}` }}
                    />
                    <LabelSmall>{item.label}</LabelSmall>
                    <ParagraphXSmall>{item.filename}</ParagraphXSmall>
                    <a href={item.url} download={item.filename}>
                      <Button size="compact" variant="secondary">
                        Download
                      </Button>
                    </a>
                  </Card>
                ))}
              </div>
            </div>
          ) : null}
        </>
      ) : null}

      {view === "approval" ? (
        <div className="grid gap-3">
          {approval.length === 0 ? (
            <ParagraphSmall>No packages waiting.</ParagraphSmall>
          ) : (
            approval.map((post) => (
              <Card key={post.id}>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <LabelSmall>{post.source_label}</LabelSmall>
                    <ParagraphXSmall className="mt-0">
                      {post.theme} · {post.branding} · {post.state}
                    </ParagraphXSmall>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {post.state === "review_required" ? (
                      <>
                        <Button
                          size="compact"
                          disabled={busy}
                          onClick={() => void act(() => approveSocialPost(post.id))}
                        >
                          Approve all
                        </Button>
                        <Button
                          size="compact"
                          variant="secondary"
                          disabled={busy}
                          onClick={() => void act(() => rejectSocialPost(post.id))}
                        >
                          Reject all
                        </Button>
                      </>
                    ) : (
                      <Button
                        size="compact"
                        disabled={busy}
                        onClick={() => void act(() => queueSocialPost(post.id))}
                      >
                        Queue approved outputs
                      </Button>
                    )}
                  </div>
                </div>
                {post.caption ? (
                  <div className="mt-2">
                    <LabelSmall>Publishing caption</LabelSmall>
                    <ParagraphSmall className="mt-0">{post.caption}</ParagraphSmall>
                  </div>
                ) : null}
                <div className="mt-3 grid grid-cols-[repeat(auto-fit,minmax(180px,1fr))] gap-2.5">
                  {post.derivatives.map((item) => (
                    <div key={item.id} className="rounded-xl border border-ink/10 p-2">
                      <img
                        src={item.url}
                        alt={item.output_key}
                        className="w-full rounded-lg object-cover"
                        style={{ aspectRatio: `${String(item.width)} / ${String(item.height)}` }}
                      />
                      <div className="mt-2 flex flex-wrap items-center justify-between gap-1.5">
                        <LabelSmall>{item.output_key}</LabelSmall>
                        {reviewTag(item.review_state)}
                      </div>
                      <ParagraphXSmall className="mt-1">{item.filename}</ParagraphXSmall>
                      {item.review_state === "review_required" ? (
                        <div className="flex flex-wrap gap-1.5">
                          <Button
                            size="compact"
                            disabled={busy}
                            onClick={() => void act(() => approveSocialDerivative(item.id))}
                          >
                            Approve
                          </Button>
                          <Button
                            size="compact"
                            variant="secondary"
                            disabled={busy}
                            onClick={() => void act(() => rejectSocialDerivative(item.id))}
                          >
                            Reject
                          </Button>
                        </div>
                      ) : null}
                    </div>
                  ))}
                </div>
              </Card>
            ))
          )}
        </div>
      ) : null}

      {view === "queue" ? (
        <div className="grid gap-2.5">
          {queue.length === 0 ? (
            <ParagraphSmall>Queue is empty.</ParagraphSmall>
          ) : (
            queue.map((job) => (
              <Card key={job.id}>
                <div className="grid grid-cols-[72px_1fr] gap-3 md:grid-cols-[96px_1fr]">
                  <img
                    src={job.derivative_url}
                    alt={job.output_key}
                    className="aspect-[4/5] w-full rounded-lg object-cover"
                  />
                  <div>
                    <LabelSmall>{job.source_label}</LabelSmall>
                    <ParagraphXSmall className="mt-0">
                      {job.channel} · {job.output_key}
                    </ParagraphXSmall>
                    <ParagraphXSmall>
                      {job.state} · {localDate(job.scheduled_at)} ·{" "}
                      {job.locked ? "manual" : "recommended"}
                    </ParagraphXSmall>
                    {job.caption ? <ParagraphXSmall>{job.caption}</ParagraphXSmall> : null}
                    {job.failure_reason ? (
                      <ParagraphXSmall>
                        Delivery: {job.failure_reason} · attempt {String(job.retry_count)}/
                        {String(job.max_attempts)}
                      </ParagraphXSmall>
                    ) : null}
                  </div>
                </div>
                <div className="mt-2.5 flex flex-wrap gap-1.5">
                  <form
                    className="flex flex-wrap gap-1.5"
                    onSubmit={(event) => {
                      event.preventDefault();
                      const form = new FormData(event.currentTarget);
                      const dateEntry = form.get("schedule-date");
                      const timeEntry = form.get("schedule-time");
                      const date = typeof dateEntry === "string" ? dateEntry : "";
                      const time = typeof timeEntry === "string" ? timeEntry : "";
                      if (!date || !time) return;
                      void act(() =>
                        scheduleSocialJob(job.id, new Date(`${date}T${time}`).toISOString()),
                      );
                    }}
                  >
                    <input
                      type="date"
                      name="schedule-date"
                      aria-label="Schedule date"
                      required
                      defaultValue={
                        job.scheduled_at
                          ? new Date(job.scheduled_at).toLocaleDateString("en-CA")
                          : undefined
                      }
                      className="min-h-[36px] rounded-lg border border-ink/15 bg-paper px-2 font-[inherit] text-ink"
                    />
                    <input
                      type="time"
                      name="schedule-time"
                      aria-label="Schedule time"
                      required
                      step={300}
                      defaultValue={
                        job.scheduled_at
                          ? new Date(job.scheduled_at).toTimeString().slice(0, 5)
                          : undefined
                      }
                      className="min-h-[36px] rounded-lg border border-ink/15 bg-paper px-2 font-[inherit] text-ink"
                    />
                    <Button size="compact" type="submit" disabled={busy}>
                      Set schedule
                    </Button>
                  </form>
                  <Button size="compact" onClick={() => void act(() => publishSocialJobNow(job.id))}>
                    Publish now
                  </Button>
                  <Button
                    size="compact"
                    variant="secondary"
                    onClick={() => void act(() => holdSocialJob(job.id))}
                  >
                    Hold
                  </Button>
                  <Button
                    size="compact"
                    variant="secondary"
                    onClick={() => void act(() => cancelSocialJob(job.id))}
                  >
                    Remove
                  </Button>
                </div>
              </Card>
            ))
          )}
        </div>
      ) : null}

      {view === "live" ? (
        <div className="grid gap-2.5">
          {live.length === 0 ? (
            <ParagraphSmall>Nothing published yet.</ParagraphSmall>
          ) : (
            live.map((job) => (
              <Card key={job.id}>
                <div className="grid grid-cols-[96px_1fr] gap-3">
                  <img
                    src={job.derivative_url}
                    alt={job.output_key}
                    className="aspect-[4/5] w-full rounded-lg object-cover"
                  />
                  <div>
                    <LabelSmall>{job.source_label}</LabelSmall>
                    <ParagraphXSmall className="mt-0">
                      {job.channel} · {job.output_key}
                    </ParagraphXSmall>
                    <ParagraphXSmall>{localDate(job.published_at)}</ParagraphXSmall>
                    <ParagraphXSmall>{job.external_post_id}</ParagraphXSmall>
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      ) : null}
    </>
  );
}

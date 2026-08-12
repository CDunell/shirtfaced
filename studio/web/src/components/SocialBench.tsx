/* eslint-disable @typescript-eslint/no-confusing-void-expression */
/** Social Studio: create → review → queue → live. */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useStyletron } from "baseui";
import { Button, KIND as BUTTON_KIND, SIZE } from "baseui/button";
import { Card, StyledBody } from "baseui/card";
import { Checkbox } from "baseui/checkbox";
import { FormControl } from "baseui/form-control";
import { Notification, KIND as NOTIFICATION_KIND } from "baseui/notification";
import { Select, type Value } from "baseui/select";
import { Tag, KIND as TAG_KIND } from "baseui/tag";
import { HeadingSmall, LabelSmall, ParagraphSmall, ParagraphXSmall } from "baseui/typography";

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
  { id: "auto", label: "Auto — choose from image" },
  { id: "light", label: "Light — ink marks" },
  { id: "dark", label: "Dark — paper marks" },
  { id: "adaptive", label: "Adaptive — backed mark" },
];

const BRANDING_OPTIONS = [
  { id: "clean", label: "Clean — no overlay" },
  { id: "fingerprint", label: "Fingerprint — minimal mark" },
  { id: "identity", label: "Identity — stronger Shirtfaced layer" },
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
    <Tag closeable={false} kind={state === "approved" ? TAG_KIND.positive : TAG_KIND.neutral}>
      {state.replace("_", " ")}
    </Tag>
  );
}

export function SocialBench(): React.JSX.Element {
  const [css, theme] = useStyletron();
  const [view, setView] = useState<SocialView>("create");
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [photoValue, setPhotoValue] = useState<Value>([]);
  const [themeValue, setThemeValue] = useState<Value>([
    { id: "auto", label: "Auto — choose from image" },
  ]);
  const [brandingValue, setBrandingValue] = useState<Value>([
    { id: "fingerprint", label: "Fingerprint — minimal mark" },
  ]);
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
    () => photos.find((item) => item.id === String(photoValue[0]?.id ?? "")) ?? null,
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
          if (first) setPhotoValue([{ id: first.id, label: first.label }]);
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
      const requested = String(themeValue[0]?.id ?? "auto") as SocialTheme;
      const chosenTheme: ResolvedTheme = requested === "auto" ? analyseTheme(source) : requested;
      const branding = String(brandingValue[0]?.id ?? "fingerprint") as Branding;
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
      const branding = String(brandingValue[0]?.id ?? "fingerprint");
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
      size={SIZE.compact}
      kind={view === id ? BUTTON_KIND.primary : BUTTON_KIND.secondary}
      onClick={() => setView(id)}
    >
      {label}
    </Button>
  );

  return (
    <>
      <PageTitle>Social Studio</PageTitle>
      <div className={css({ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "18px" })}>
        {nav("create", "Create")}
        {nav("approval", `Approval ${String(approval.length)}`)}
        {nav("queue", `Queue ${String(queue.length)}`)}
        {nav("live", `Live ${String(live.length)}`)}
      </div>
      {error ? <Notification kind={NOTIFICATION_KIND.negative}>{error}</Notification> : null}

      {view === "create" ? (
        <>
          <ParagraphSmall color={theme.colors.contentSecondary} marginTop={0}>
            Pick the asset. Pick the outputs. GO makes the package; Save for review freezes the
            exact files.
          </ParagraphSmall>
          <div
            className={css({
              display: "grid",
              gridTemplateColumns: "minmax(280px, 1.2fr) minmax(260px, .8fr)",
              gap: "16px",
              alignItems: "start",
              "@media screen and (max-width: 760px)": { gridTemplateColumns: "1fr" },
            })}
          >
            <Card>
              <StyledBody>
                <FormControl label="Source asset">
                  <Select
                    clearable={false}
                    searchable
                    options={photos.map((item) => ({ id: item.id, label: item.label }))}
                    value={photoValue}
                    onChange={({ value }) => {
                      setPhotoValue(value);
                      setSavedId(null);
                    }}
                  />
                </FormControl>
                <Button
                  size={SIZE.compact}
                  kind={BUTTON_KIND.secondary}
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
                        setPhotoValue([{ id: uploaded.id, label: uploaded.label }]);
                      });
                    event.currentTarget.value = "";
                  }}
                />
                {photo ? (
                  <img
                    src={photo.url}
                    alt="Selected source"
                    className={css({
                      width: "100%",
                      aspectRatio: "4 / 5",
                      objectFit: "cover",
                      borderRadius: "16px",
                      marginTop: "12px",
                    })}
                  />
                ) : null}
                {photo ? (
                  <div
                    className={css({
                      display: "flex",
                      gap: "6px",
                      flexWrap: "wrap",
                      marginTop: "8px",
                    })}
                  >
                    <Tag closeable={false} kind={TAG_KIND.neutral}>
                      {String(photo.width)}×{String(photo.height)}
                    </Tag>
                    <Tag closeable={false} kind={TAG_KIND.neutral}>
                      {photo.uploaded ? "uploaded" : "world asset"}
                    </Tag>
                  </div>
                ) : null}
              </StyledBody>
            </Card>
            <Card>
              <StyledBody>
                <FormControl label="Contrast treatment">
                  <Select
                    clearable={false}
                    options={THEME_OPTIONS}
                    value={themeValue}
                    onChange={({ value }) => setThemeValue(value)}
                  />
                </FormControl>
                <FormControl label="Branding">
                  <Select
                    clearable={false}
                    options={BRANDING_OPTIONS}
                    value={brandingValue}
                    onChange={({ value }) => setBrandingValue(value)}
                  />
                </FormControl>
                <LabelSmall>Outputs</LabelSmall>
                <div className={css({ marginTop: "8px", marginBottom: "16px" })}>
                  {OUTPUTS.map((spec) => (
                    <Checkbox
                      key={spec.key}
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
                    className={css({
                      width: "100%",
                      boxSizing: "border-box",
                      padding: "10px",
                      font: "inherit",
                      borderRadius: "8px",
                      border: `1px solid ${theme.colors.borderOpaque}`,
                      backgroundColor: theme.colors.backgroundPrimary,
                      color: theme.colors.contentPrimary,
                    })}
                  />
                </FormControl>
                <Button
                  disabled={!photo || selectedOutputs.size === 0}
                  isLoading={busy}
                  onClick={() => void go()}
                  overrides={{
                    BaseButton: { style: { width: "100%", minHeight: "52px", fontWeight: 700 } },
                  }}
                >
                  GO
                </Button>
              </StyledBody>
            </Card>
          </div>
          {exports.length > 0 ? (
            <div className={css({ marginTop: "22px" })}>
              <div
                className={css({
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  gap: "10px",
                  flexWrap: "wrap",
                })}
              >
                <div>
                  <HeadingSmall marginBottom={0}>Ready</HeadingSmall>
                  <ParagraphXSmall marginTop={0}>
                    {resolvedTheme ? `Resolved ${resolvedTheme}.` : ""}
                  </ParagraphXSmall>
                </div>
                <Button
                  disabled={Boolean(savedId)}
                  isLoading={busy}
                  onClick={() => void saveForReview()}
                >
                  {savedId ? "Saved for review" : "Save for review"}
                </Button>
              </div>
              <div
                className={css({
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(210px, 1fr))",
                  gap: "12px",
                  marginTop: "10px",
                })}
              >
                {exports.map((item) => (
                  <Card key={item.key}>
                    <StyledBody>
                      <img
                        src={item.url}
                        alt={item.label}
                        className={css({
                          width: "100%",
                          aspectRatio: `${String(item.width)} / ${String(item.height)}`,
                          objectFit: "cover",
                          borderRadius: "10px",
                        })}
                      />
                      <LabelSmall>{item.label}</LabelSmall>
                      <ParagraphXSmall>{item.filename}</ParagraphXSmall>
                      <a href={item.url} download={item.filename}>
                        <Button size={SIZE.mini} kind={BUTTON_KIND.secondary}>
                          Download
                        </Button>
                      </a>
                    </StyledBody>
                  </Card>
                ))}
              </div>
            </div>
          ) : null}
        </>
      ) : null}

      {view === "approval" ? (
        <div className={css({ display: "grid", gap: "12px" })}>
          {approval.length === 0 ? (
            <ParagraphSmall>No packages waiting.</ParagraphSmall>
          ) : (
            approval.map((post) => (
              <Card key={post.id}>
                <StyledBody>
                  <div
                    className={css({
                      display: "flex",
                      justifyContent: "space-between",
                      gap: "12px",
                      flexWrap: "wrap",
                      alignItems: "flex-start",
                    })}
                  >
                    <div>
                      <LabelSmall>{post.source_label}</LabelSmall>
                      <ParagraphXSmall marginTop={0}>
                        {post.theme} · {post.branding} · {post.state}
                      </ParagraphXSmall>
                    </div>
                    <div className={css({ display: "flex", gap: "6px", flexWrap: "wrap" })}>
                      {post.state === "review_required" ? (
                        <>
                          <Button
                            size={SIZE.compact}
                            disabled={busy}
                            onClick={() => void act(() => approveSocialPost(post.id))}
                          >
                            Approve all
                          </Button>
                          <Button
                            size={SIZE.compact}
                            kind={BUTTON_KIND.secondary}
                            disabled={busy}
                            onClick={() => void act(() => rejectSocialPost(post.id))}
                          >
                            Reject all
                          </Button>
                        </>
                      ) : (
                        <Button
                          size={SIZE.compact}
                          disabled={busy}
                          onClick={() => void act(() => queueSocialPost(post.id))}
                        >
                          Queue approved outputs
                        </Button>
                      )}
                    </div>
                  </div>
                  {post.caption ? (
                    <div className={css({ marginTop: "8px" })}>
                      <LabelSmall>Publishing caption</LabelSmall>
                      <ParagraphSmall marginTop={0}>{post.caption}</ParagraphSmall>
                    </div>
                  ) : null}
                  <div
                    className={css({
                      display: "grid",
                      gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                      gap: "10px",
                      marginTop: "12px",
                    })}
                  >
                    {post.derivatives.map((item) => (
                      <div
                        key={item.id}
                        className={css({
                          border: `1px solid ${theme.colors.borderOpaque}`,
                          borderRadius: "12px",
                          padding: "8px",
                        })}
                      >
                        <img
                          src={item.url}
                          alt={item.output_key}
                          className={css({
                            width: "100%",
                            aspectRatio: `${String(item.width)} / ${String(item.height)}`,
                            objectFit: "cover",
                            borderRadius: "8px",
                          })}
                        />
                        <div
                          className={css({
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "center",
                            gap: "6px",
                            marginTop: "8px",
                            flexWrap: "wrap",
                          })}
                        >
                          <LabelSmall>{item.output_key}</LabelSmall>
                          {reviewTag(item.review_state)}
                        </div>
                        <ParagraphXSmall marginTop={theme.sizing.scale100}>
                          {item.filename}
                        </ParagraphXSmall>
                        {item.review_state === "review_required" ? (
                          <div className={css({ display: "flex", gap: "6px", flexWrap: "wrap" })}>
                            <Button
                              size={SIZE.mini}
                              disabled={busy}
                              onClick={() => void act(() => approveSocialDerivative(item.id))}
                            >
                              Approve
                            </Button>
                            <Button
                              size={SIZE.mini}
                              kind={BUTTON_KIND.secondary}
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
                </StyledBody>
              </Card>
            ))
          )}
        </div>
      ) : null}

      {view === "queue" ? (
        <div className={css({ display: "grid", gap: "10px" })}>
          {queue.length === 0 ? (
            <ParagraphSmall>Queue is empty.</ParagraphSmall>
          ) : (
            queue.map((job) => (
              <Card key={job.id}>
                <StyledBody>
                  <div
                    className={css({
                      display: "grid",
                      gridTemplateColumns: "96px 1fr",
                      gap: "12px",
                      "@media screen and (max-width: 520px)": { gridTemplateColumns: "72px 1fr" },
                    })}
                  >
                    <img
                      src={job.derivative_url}
                      alt={job.output_key}
                      className={css({
                        width: "100%",
                        aspectRatio: "4 / 5",
                        objectFit: "cover",
                        borderRadius: "8px",
                      })}
                    />
                    <div>
                      <LabelSmall>{job.source_label}</LabelSmall>
                      <ParagraphXSmall marginTop={0}>
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
                  <div
                    className={css({
                      display: "flex",
                      gap: "6px",
                      flexWrap: "wrap",
                      marginTop: "10px",
                    })}
                  >
                    <form
                      className={css({ display: "flex", gap: "6px", flexWrap: "wrap" })}
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
                        className={css({
                          minHeight: "36px",
                          padding: "0 8px",
                          borderRadius: "8px",
                          border: `1px solid ${theme.colors.borderOpaque}`,
                          backgroundColor: theme.colors.backgroundPrimary,
                          color: theme.colors.contentPrimary,
                          font: "inherit",
                        })}
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
                        className={css({
                          minHeight: "36px",
                          padding: "0 8px",
                          borderRadius: "8px",
                          border: `1px solid ${theme.colors.borderOpaque}`,
                          backgroundColor: theme.colors.backgroundPrimary,
                          color: theme.colors.contentPrimary,
                          font: "inherit",
                        })}
                      />
                      <Button size={SIZE.mini} type="submit" disabled={busy}>
                        Set schedule
                      </Button>
                    </form>
                    <Button
                      size={SIZE.mini}
                      onClick={() => void act(() => publishSocialJobNow(job.id))}
                    >
                      Publish now
                    </Button>
                    <Button
                      size={SIZE.mini}
                      kind={BUTTON_KIND.secondary}
                      onClick={() => void act(() => holdSocialJob(job.id))}
                    >
                      Hold
                    </Button>
                    <Button
                      size={SIZE.mini}
                      kind={BUTTON_KIND.secondary}
                      onClick={() => void act(() => cancelSocialJob(job.id))}
                    >
                      Remove
                    </Button>
                  </div>
                </StyledBody>
              </Card>
            ))
          )}
        </div>
      ) : null}

      {view === "live" ? (
        <div className={css({ display: "grid", gap: "10px" })}>
          {live.length === 0 ? (
            <ParagraphSmall>Nothing published yet.</ParagraphSmall>
          ) : (
            live.map((job) => (
              <Card key={job.id}>
                <StyledBody>
                  <div
                    className={css({
                      display: "grid",
                      gridTemplateColumns: "96px 1fr",
                      gap: "12px",
                    })}
                  >
                    <img
                      src={job.derivative_url}
                      alt={job.output_key}
                      className={css({
                        width: "100%",
                        aspectRatio: "4 / 5",
                        objectFit: "cover",
                        borderRadius: "8px",
                      })}
                    />
                    <div>
                      <LabelSmall>{job.source_label}</LabelSmall>
                      <ParagraphXSmall marginTop={0}>
                        {job.channel} · {job.output_key}
                      </ParagraphXSmall>
                      <ParagraphXSmall>{localDate(job.published_at)}</ParagraphXSmall>
                      <ParagraphXSmall>{job.external_post_id}</ParagraphXSmall>
                    </div>
                  </div>
                </StyledBody>
              </Card>
            ))
          )}
        </div>
      ) : null}
    </>
  );
}

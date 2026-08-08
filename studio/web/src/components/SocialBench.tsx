/**
 * Social export bench.
 *
 * Pick an approved/uploaded photograph, choose outputs, press GO. The browser
 * crops the image, chooses the right V3 contrast treatment when set to Auto,
 * applies the real generated Shirtfaced SVG and emits platform-sized files.
 */

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

import { ApiError, fetchPhotos, uploadPhoto, type Photo } from "../api/client";

type SocialTheme = "auto" | "light" | "dark" | "adaptive";
type ResolvedTheme = Exclude<SocialTheme, "auto">;
type Branding = "clean" | "fingerprint" | "identity";
type OutputKey = "instagram_feed" | "instagram_story" | "reel_cover" | "tiktok_cover";

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
  {
    key: "reel_cover",
    label: "Reel cover",
    width: 1080,
    height: 1920,
    suffix: "REEL-COVER",
  },
  {
    key: "tiktok_cover",
    label: "TikTok cover",
    width: 1080,
    height: 1920,
    suffix: "TIKTOK-COVER",
  },
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

function loadImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => {
      resolve(image);
    };
    image.onerror = () => {
      reject(new Error("The source image could not be loaded."));
    };
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
  const deviation = Math.sqrt(variance);
  if (deviation > 58 && mean > 65 && mean < 205) return "adaptive";
  return mean >= 145 ? "light" : "dark";
}

function overlayPath(theme: ResolvedTheme, branding: Branding, output: OutputKey): string | null {
  if (branding === "clean") return null;

  const vertical = output !== "instagram_feed";
  if (!vertical) {
    if (branding === "fingerprint") {
      return `/social-assets/v3/${theme}-corner-mark-4x5.svg`;
    }
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
      (blob) => {
        if (blob) resolve(blob);
        else reject(new Error("The browser could not encode the export."));
      },
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
  files.forEach((item) => {
    URL.revokeObjectURL(item.url);
  });
}

export function SocialBench(): React.JSX.Element {
  const [css, theme] = useStyletron();
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [photoValue, setPhotoValue] = useState<Value>([]);
  const [themeValue, setThemeValue] = useState<Value>([
    { id: "auto", label: "Auto — choose from image" },
  ]);
  const [brandingValue, setBrandingValue] = useState<Value>([
    { id: "fingerprint", label: "Fingerprint — minimal mark" },
  ]);
  const [selectedOutputs, setSelectedOutputs] = useState<Set<OutputKey>>(
    new Set(["instagram_feed", "instagram_story", "reel_cover", "tiktok_cover"]),
  );
  const [resolvedTheme, setResolvedTheme] = useState<ResolvedTheme | null>(null);
  const [exports, setExports] = useState<ExportedFile[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
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

  useEffect(() => {
    const timer = setTimeout(() => {
      refreshPhotos()
        .then((found) => {
          const first = found[0];
          if (first) {
            setPhotoValue((current) =>
              current.length > 0 ? current : [{ id: first.id, label: first.label }],
            );
          }
        })
        .catch((cause: unknown) => {
          setError(describe(cause));
        });
    }, 0);
    return () => {
      clearTimeout(timer);
    };
  }, [refreshPhotos]);

  const choosePhoto = useCallback((value: Value) => {
    setPhotoValue(value);
    setExports((old) => {
      releaseExports(old);
      return [];
    });
    setResolvedTheme(null);
  }, []);

  const onUpload = useCallback(
    async (file: File) => {
      setBusy(true);
      setError(null);
      try {
        const uploaded = await uploadPhoto(file);
        await refreshPhotos();
        choosePhoto([{ id: uploaded.id, label: uploaded.label }]);
      } catch (cause) {
        setError(describe(cause));
      } finally {
        setBusy(false);
      }
    },
    [choosePhoto, refreshPhotos],
  );

  const go = useCallback(async () => {
    if (!photo || selectedOutputs.size === 0) return;

    setBusy(true);
    setError(null);
    try {
      const source = await loadImage(photo.url);
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
        if (overlay) {
          const mark = await loadImage(overlay);
          ctx.drawImage(mark, 0, 0, spec.width, spec.height);
        }
        const blob = await blobFromCanvas(canvas);
        const filename = `SF_${cleanName(photo.label)}_${spec.suffix}.jpg`;
        made.push({
          ...spec,
          url: URL.createObjectURL(blob),
          filename,
          theme: chosenTheme,
        });
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

  const downloadAll = useCallback(() => {
    for (const item of exports) {
      const link = document.createElement("a");
      link.href = item.url;
      link.download = item.filename;
      link.click();
    }
  }, [exports]);

  return (
    <>
      <HeadingSmall marginTop={0} marginBottom={theme.sizing.scale300}>
        Social
      </HeadingSmall>
      <ParagraphSmall color={theme.colors.contentSecondary} marginTop={0}>
        Pick the asset. Pick the outputs. GO does the crop, contrast treatment, Shirtfaced layer and
        filenames.
      </ParagraphSmall>

      {error ? <Notification kind={NOTIFICATION_KIND.negative}>{error}</Notification> : null}

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
            <div
              className={css({
                display: "flex",
                justifyContent: "space-between",
                gap: "8px",
                alignItems: "end",
                flexWrap: "wrap",
              })}
            >
              <div className={css({ flex: "1 1 280px" })}>
                <FormControl
                  label="Source asset"
                  caption="Approved World frames and anything uploaded to Studio"
                >
                  <Select
                    clearable={false}
                    searchable
                    options={photos.map((item) => ({ id: item.id, label: item.label }))}
                    value={photoValue}
                    onChange={({ value }) => {
                      choosePhoto(value);
                    }}
                  />
                </FormControl>
              </div>
              <Button
                size={SIZE.compact}
                kind={BUTTON_KIND.secondary}
                disabled={busy}
                onClick={() => {
                  uploadInput.current?.click();
                }}
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
                  if (file) void onUpload(file);
                  event.currentTarget.value = "";
                }}
              />
            </div>

            {photo ? (
              <div
                className={css({
                  marginTop: "8px",
                  borderRadius: "16px",
                  overflow: "hidden",
                  backgroundColor: theme.colors.backgroundSecondary,
                  aspectRatio: "4 / 5",
                  display: "grid",
                  placeItems: "center",
                })}
              >
                <img
                  src={photo.url}
                  alt="Selected source"
                  className={css({
                    width: "100%",
                    height: "100%",
                    objectFit: "cover",
                  })}
                />
              </div>
            ) : (
              <div
                className={css({
                  padding: "48px 16px",
                  textAlign: "center",
                  color: theme.colors.contentSecondary,
                })}
              >
                No source asset yet.
              </div>
            )}

            {photo ? (
              <div
                className={css({
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "6px",
                  marginTop: "10px",
                })}
              >
                <Tag closeable={false} kind={TAG_KIND.neutral}>
                  {String(photo.width)}×{String(photo.height)}
                </Tag>
                <Tag closeable={false} kind={TAG_KIND.neutral}>
                  {photo.uploaded ? "uploaded" : "world asset"}
                </Tag>
                {photo.from_prompt ? (
                  <Tag closeable={false} kind={TAG_KIND.neutral}>
                    {photo.from_prompt.shot_external_id} / v{String(photo.from_prompt.variation)}
                  </Tag>
                ) : null}
              </div>
            ) : null}
          </StyledBody>
        </Card>

        <Card>
          <StyledBody>
            <FormControl
              label="Contrast treatment"
              caption="Auto samples the actual image; it does not assume nightlife."
            >
              <Select
                clearable={false}
                options={THEME_OPTIONS}
                value={themeValue}
                onChange={({ value }) => {
                  setThemeValue(value);
                }}
              />
            </FormControl>
            <FormControl label="Branding">
              <Select
                clearable={false}
                options={BRANDING_OPTIONS}
                value={brandingValue}
                onChange={({ value }) => {
                  setBrandingValue(value);
                }}
              />
            </FormControl>

            <LabelSmall>Outputs</LabelSmall>
            <div className={css({ marginTop: "8px", marginBottom: "16px" })}>
              {OUTPUTS.map((spec) => (
                <Checkbox
                  key={spec.key}
                  checked={selectedOutputs.has(spec.key)}
                  onChange={() => {
                    setSelectedOutputs((old) => {
                      const next = new Set(old);
                      if (next.has(spec.key)) next.delete(spec.key);
                      else next.add(spec.key);
                      return next;
                    });
                  }}
                >
                  {spec.label}{" "}
                  <span className={css({ color: theme.colors.contentTertiary })}>
                    {String(spec.width)}×{String(spec.height)}
                  </span>
                </Checkbox>
              ))}
            </div>

            <Button
              disabled={!photo || selectedOutputs.size === 0}
              isLoading={busy}
              onClick={() => {
                void go();
              }}
              overrides={{
                BaseButton: {
                  style: { width: "100%", minHeight: "52px", fontSize: "18px", fontWeight: 700 },
                },
              }}
            >
              GO
            </Button>
            <ParagraphXSmall color={theme.colors.contentSecondary}>
              Nothing is published. GO only makes finished files.
            </ParagraphXSmall>
          </StyledBody>
        </Card>
      </div>

      {exports.length > 0 ? (
        <div className={css({ marginTop: theme.sizing.scale800 })}>
          <div
            className={css({
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: "8px",
              flexWrap: "wrap",
            })}
          >
            <div>
              <HeadingSmall marginBottom={0}>Ready</HeadingSmall>
              <ParagraphXSmall color={theme.colors.contentSecondary} marginTop={0}>
                {resolvedTheme ? `Resolved ${resolvedTheme}. ` : ""}
                {String(exports.length)} export{exports.length === 1 ? "" : "s"}.
              </ParagraphXSmall>
            </div>
            <Button size={SIZE.compact} kind={BUTTON_KIND.secondary} onClick={downloadAll}>
              Download all
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
                      display: "block",
                      marginBottom: "8px",
                    })}
                  />
                  <LabelSmall>{item.label}</LabelSmall>
                  <ParagraphXSmall color={theme.colors.contentSecondary}>
                    {item.filename}
                  </ParagraphXSmall>
                  <a
                    href={item.url}
                    download={item.filename}
                    className={css({ color: "inherit", textDecoration: "none" })}
                  >
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
  );
}

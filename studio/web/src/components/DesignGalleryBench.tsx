import { useEffect, useState } from "react";
import { Select } from "baseui/select";
import { Button, SIZE, KIND } from "baseui/button";
import { ParagraphSmall, ParagraphXSmall, LabelXSmall } from "baseui/typography";
import { useStyletron } from "baseui";

import {
  fetchGenerations,
  generationImageUrl,
  type GenerationSample,
  type GenerationStatus,
} from "../api/concepts";
import { CopyButton, PageTitle } from "./chrome";

const MOBILE_PAGE_SIZE = 16;
const DESKTOP_PAGE_SIZE = 30;
// 1024px matches the app shell's own <main> max-width (App.tsx) -- the point
// past which the grid has real room to breathe, not an arbitrary number.
const DESKTOP_BREAKPOINT = "(min-width: 1024px)";

function useIsDesktop(): boolean {
  const [isDesktop, setIsDesktop] = useState(
    () => typeof window !== "undefined" && window.matchMedia(DESKTOP_BREAKPOINT).matches,
  );
  useEffect(() => {
    const mql = window.matchMedia(DESKTOP_BREAKPOINT);
    const onChange = (e: MediaQueryListEvent): void => {
      setIsDesktop(e.matches);
    };
    mql.addEventListener("change", onChange);
    return () => {
      mql.removeEventListener("change", onChange);
    };
  }, []);
  return isDesktop;
}

const STATUS_OPTIONS: { id: GenerationStatus | ""; label: string }[] = [
  { id: "", label: "All statuses" },
  { id: "kept", label: "Kept" },
  { id: "dropped", label: "Dropped" },
];

export function DesignGalleryBench(): React.JSX.Element {
  const [css, theme] = useStyletron();
  const isDesktop = useIsDesktop();
  const pageSize = isDesktop ? DESKTOP_PAGE_SIZE : MOBILE_PAGE_SIZE;
  const [page, setPage] = useState(1);
  const [tradition, setTradition] = useState("");
  const [statusFilter, setStatusFilter] = useState<GenerationStatus | "">("");
  const [items, setItems] = useState<GenerationSample[]>([]);
  const [total, setTotal] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    setBusy(true);
    setError("");
    fetchGenerations(page, pageSize, tradition || undefined, statusFilter || undefined)
      .then((result) => {
        if (cancelled) return;
        setItems(result.items);
        setTotal(result.total);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Couldn't load the gallery.");
      })
      .finally(() => {
        if (!cancelled) setBusy(false);
      });
    return () => {
      cancelled = true;
    };
  }, [page, pageSize, tradition, statusFilter]);

  useEffect(() => {
    setPage(1);
  }, [tradition, statusFilter, pageSize]);

  useEffect(() => {
    if (lightboxIndex === null) return;
    function onKey(e: KeyboardEvent): void {
      if (e.key === "Escape") setLightboxIndex(null);
      if (e.key === "ArrowRight") setLightboxIndex((i) => (i === null ? i : Math.min(i + 1, items.length - 1)));
      if (e.key === "ArrowLeft") setLightboxIndex((i) => (i === null ? i : Math.max(i - 1, 0)));
    }
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("keydown", onKey);
    };
  }, [lightboxIndex, items.length]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const traditions = Array.from(new Set(items.map((i) => i.tradition))).sort();
  const active = lightboxIndex !== null ? items[lightboxIndex] : null;

  return (
    <div>
      <PageTitle>Gallery</PageTitle>
      <ParagraphSmall marginTop={0} color="mono600">
        Every batch-pool concept that's actually been rendered and looked at — the image and
        the exact prompt that produced it, kept whether or not the concept made the cut.
        Reference material, not a live feed.
      </ParagraphSmall>

      <div
        className={css({
          display: "flex",
          gap: "16px",
          alignItems: "center",
          marginTop: "12px",
          marginBottom: "20px",
          flexWrap: "wrap",
        })}
      >
        <div className={css({ minWidth: "200px" })}>
          <Select
            options={[{ id: "", label: "All traditions" }, ...traditions.map((t) => ({ id: t, label: t }))]}
            value={[{ id: tradition, label: tradition || "All traditions" }]}
            onChange={({ value }) => {
              const picked = value[0];
              setTradition(picked ? String(picked.id) : "");
            }}
            clearable={false}
            searchable
            size={SIZE.compact}
          />
        </div>
        <div className={css({ minWidth: "160px" })}>
          <Select
            options={STATUS_OPTIONS}
            value={[STATUS_OPTIONS.find((o) => o.id === statusFilter) ?? STATUS_OPTIONS[0]!]}
            onChange={({ value }) => {
              const picked = value[0];
              setStatusFilter((picked ? String(picked.id) : "") as GenerationStatus | "");
            }}
            clearable={false}
            size={SIZE.compact}
          />
        </div>
        <ParagraphXSmall color="mono600" margin={0}>
          {total} render{total === 1 ? "" : "s"}
        </ParagraphXSmall>
      </div>

      {error ? <ParagraphSmall color="negative">{error}</ParagraphSmall> : null}

      <div
        className={css({
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
          gap: "14px",
          opacity: busy ? 0.5 : 1,
          transition: "opacity 120ms",
        })}
      >
        {items.map((item, index) => (
          <button
            key={item.id}
            onClick={() => {
              setLightboxIndex(index);
            }}
            className={css({
              appearance: "none",
              border: `1px solid ${item.status === "dropped" ? theme.colors.negative400 : "transparent"}`,
              borderRadius: "6px",
              padding: 0,
              overflow: "hidden",
              cursor: "pointer",
              background: theme.colors.backgroundSecondary,
              textAlign: "left",
              display: "flex",
              flexDirection: "column",
            })}
          >
            <img
              src={generationImageUrl(item.id, "thumb")}
              alt={`${item.tradition} concept render`}
              loading="lazy"
              className={css({ width: "100%", aspectRatio: "1 / 1", objectFit: "cover", display: "block" })}
            />
            <div className={css({ padding: "8px 10px" })}>
              <div className={css({ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "6px" })}>
                <LabelXSmall color="mono600" $style={{ textTransform: "uppercase", letterSpacing: "0.04em" }}>
                  {item.tradition}
                </LabelXSmall>
                {item.status === "dropped" ? (
                  <LabelXSmall color="negative" $style={{ textTransform: "uppercase", fontSize: "10px" }}>
                    dropped
                  </LabelXSmall>
                ) : null}
              </div>
            </div>
          </button>
        ))}
      </div>

      {!busy && items.length === 0 ? (
        <ParagraphSmall color="mono600" marginTop="24px">
          Nothing matches those filters yet.
        </ParagraphSmall>
      ) : null}

      <div
        className={css({
          display: "flex",
          gap: "12px",
          alignItems: "center",
          justifyContent: "center",
          marginTop: "28px",
        })}
      >
        <Button
          size={SIZE.compact}
          kind={KIND.tertiary}
          disabled={page <= 1}
          onClick={() => {
            setPage((p) => Math.max(1, p - 1));
          }}
        >
          Previous
        </Button>
        <ParagraphXSmall color="mono600" margin={0}>
          Page {page} of {totalPages}
        </ParagraphXSmall>
        <Button
          size={SIZE.compact}
          kind={KIND.tertiary}
          disabled={page >= totalPages}
          onClick={() => {
            setPage((p) => Math.min(totalPages, p + 1));
          }}
        >
          Next
        </Button>
      </div>

      {active ? (
        <div
          role="dialog"
          aria-modal="true"
          onClick={() => {
            setLightboxIndex(null);
          }}
          className={css({
            position: "fixed",
            inset: 0,
            zIndex: 100,
            background: "rgba(0, 0, 0, 0.82)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "24px",
          })}
        >
          <div
            onClick={(e) => {
              e.stopPropagation();
            }}
            className={css({
              display: "flex",
              flexDirection: "column",
              gap: "16px",
              maxWidth: "1000px",
              width: "100%",
              maxHeight: "92vh",
            })}
          >
            <div className={css({ display: "flex", gap: "20px", flexWrap: "wrap", overflow: "auto" })}>
              <img
                src={generationImageUrl(active.id, "full")}
                alt={`${active.tradition} concept render, full size`}
                className={css({
                  maxWidth: "min(480px, 100%)",
                  maxHeight: "72vh",
                  objectFit: "contain",
                  borderRadius: "6px",
                  flexShrink: 0,
                })}
              />
              <div className={css({ display: "flex", flexDirection: "column", gap: "10px", minWidth: "260px", flex: 1 })}>
                <div className={css({ display: "flex", gap: "8px", alignItems: "center" })}>
                  <LabelXSmall
                    color="backgroundPrimary"
                    $style={{
                      background: theme.colors.contentPrimary,
                      padding: "3px 8px",
                      borderRadius: "3px",
                      textTransform: "uppercase",
                      letterSpacing: "0.04em",
                    }}
                  >
                    {active.tradition}
                  </LabelXSmall>
                  {active.status === "dropped" ? (
                    <LabelXSmall color="negative" $style={{ textTransform: "uppercase" }}>
                      dropped
                    </LabelXSmall>
                  ) : null}
                  <ParagraphXSmall color="mono600" margin={0}>
                    {active.batch}
                  </ParagraphXSmall>
                </div>
                <ParagraphSmall margin={0}>{active.concept_text}</ParagraphSmall>
                {active.drop_reason ? (
                  <ParagraphXSmall
                    color="negative"
                    margin={0}
                    $style={{
                      background: "rgba(220, 60, 40, 0.1)",
                      padding: "8px 10px",
                      borderRadius: "4px",
                    }}
                  >
                    {active.drop_reason}
                  </ParagraphXSmall>
                ) : null}
                <div
                  className={css({
                    fontFamily: "monospace",
                    fontSize: "12px",
                    lineHeight: "1.5",
                    whiteSpace: "pre-wrap",
                    background: theme.colors.backgroundSecondary,
                    borderRadius: "4px",
                    padding: "10px",
                    maxHeight: "220px",
                    overflow: "auto",
                  })}
                >
                  {active.prompt}
                </div>
                <div className={css({ display: "flex", gap: "10px" })}>
                  <CopyButton text={active.prompt} label="Copy prompt" />
                  <Button size={SIZE.compact} kind={KIND.tertiary} onClick={() => setLightboxIndex(null)}>
                    Close
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

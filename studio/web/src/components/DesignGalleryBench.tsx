import { useEffect, useState } from "react";
import { Button, cx, LabelXSmall, ParagraphSmall, ParagraphXSmall, Select } from "./ui";

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

const STATUS_OPTIONS: { value: GenerationStatus | ""; label: string }[] = [
  { value: "", label: "All statuses" },
  { value: "kept", label: "Kept" },
  { value: "dropped", label: "Dropped" },
];

export function DesignGalleryBench(): React.JSX.Element {
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
      <ParagraphSmall className="mt-0 text-ink/60">
        Every batch-pool concept that's actually been rendered and looked at — the image and
        the exact prompt that produced it, kept whether or not the concept made the cut.
        Reference material, not a live feed.
      </ParagraphSmall>

      <div className="mt-3 mb-5 flex flex-wrap items-center gap-4">
        <div className="min-w-[200px]">
          <Select
            options={[
              { value: "", label: "All traditions" },
              ...traditions.map((t) => ({ value: t, label: t })),
            ]}
            value={tradition}
            onChange={(value) => {
              setTradition(value);
            }}
            placeholder="All traditions"
          />
        </div>
        <div className="min-w-[160px]">
          <Select
            options={STATUS_OPTIONS}
            value={statusFilter}
            onChange={(value) => {
              setStatusFilter(value as GenerationStatus | "");
            }}
          />
        </div>
        <ParagraphXSmall className="m-0 text-ink/60">
          {total} render{total === 1 ? "" : "s"}
        </ParagraphXSmall>
      </div>

      {error ? <ParagraphSmall className="text-coral">{error}</ParagraphSmall> : null}

      <div
        className="grid gap-3.5 transition-opacity duration-[120ms]"
        style={{ gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", opacity: busy ? 0.5 : 1 }}
      >
        {items.map((item, index) => (
          <button
            key={item.id}
            onClick={() => {
              setLightboxIndex(index);
            }}
            className={cx(
              "flex appearance-none flex-col overflow-hidden rounded-[6px] border bg-paper-2 p-0 text-left cursor-pointer",
              item.status === "dropped" ? "border-coral" : "border-transparent",
            )}
          >
            <img
              src={generationImageUrl(item.id, "thumb")}
              alt={`${item.tradition} concept render`}
              loading="lazy"
              className="block aspect-square w-full object-cover"
            />
            <div className="px-2.5 py-2">
              <div className="flex items-center justify-between gap-1.5">
                <LabelXSmall className="text-ink/60 uppercase tracking-[0.04em]">
                  {item.tradition}
                </LabelXSmall>
                {item.status === "dropped" ? (
                  <LabelXSmall className="text-[10px] text-coral uppercase">dropped</LabelXSmall>
                ) : null}
              </div>
            </div>
          </button>
        ))}
      </div>

      {!busy && items.length === 0 ? (
        <ParagraphSmall className="mt-6 text-ink/60">
          Nothing matches those filters yet.
        </ParagraphSmall>
      ) : null}

      <div className="mt-7 flex items-center justify-center gap-3">
        <Button
          size="compact"
          variant="ghost"
          disabled={page <= 1}
          onClick={() => {
            setPage((p) => Math.max(1, p - 1));
          }}
        >
          Previous
        </Button>
        <ParagraphXSmall className="m-0 text-ink/60">
          Page {page} of {totalPages}
        </ParagraphXSmall>
        <Button
          size="compact"
          variant="ghost"
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
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/[0.82] p-6"
        >
          <div
            onClick={(e) => {
              e.stopPropagation();
            }}
            className="flex max-h-[92vh] w-full max-w-[1000px] flex-col gap-4"
          >
            <div className="flex flex-wrap gap-5 overflow-auto">
              <img
                src={generationImageUrl(active.id, "full")}
                alt={`${active.tradition} concept render, full size`}
                className="max-h-[72vh] max-w-[min(480px,100%)] shrink-0 rounded-[6px] object-contain"
              />
              <div className="flex min-w-[260px] flex-1 flex-col gap-2.5">
                <div className="flex items-center gap-2">
                  <LabelXSmall className="rounded-[3px] bg-ink px-2 py-[3px] text-paper uppercase tracking-[0.04em]">
                    {active.tradition}
                  </LabelXSmall>
                  {active.status === "dropped" ? (
                    <LabelXSmall className="text-coral uppercase">dropped</LabelXSmall>
                  ) : null}
                  <ParagraphXSmall className="m-0 text-ink/60">{active.batch}</ParagraphXSmall>
                </div>
                <ParagraphSmall className="m-0">{active.concept_text}</ParagraphSmall>
                {active.drop_reason ? (
                  <ParagraphXSmall className="m-0 rounded-[4px] bg-coral/10 px-2.5 py-2 text-coral">
                    {active.drop_reason}
                  </ParagraphXSmall>
                ) : null}
                <div className="max-h-[220px] overflow-auto rounded-[4px] bg-paper-2 p-2.5 font-mono text-[12px] leading-[1.5] whitespace-pre-wrap">
                  {active.prompt}
                </div>
                <div className="flex gap-2.5">
                  <CopyButton text={active.prompt} label="Copy prompt" />
                  <Button size="compact" variant="ghost" onClick={() => setLightboxIndex(null)}>
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

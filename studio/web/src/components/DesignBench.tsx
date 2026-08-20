/**
 * Measuring a design against the review scorecard.
 *
 * Drop a design in and it is measured -- print coverage, ink count, placement,
 * and the scorecard's own thumbnail and blur tests -- then reported as the
 * hard gates and weighted categories those measurements actually support.
 *
 * Scoring, banding and release status are decided by
 * ``admin/src/design-system/workflow.ts``'s ``evaluateReview`` /
 * ``nextStatusForReview``, not here -- this screen never shows a total or a
 * verdict, only what was measured and how much of the rubric that covers.
 * Measurement fills the gates it can answer honestly and leaves the rest
 * untested; an untested gate blocks release in ``evaluateReview`` exactly as
 * a failed one does. What this produces is the start of a review, with the
 * measurable half already done, not a decision.
 */

import { useCallback, useEffect, useRef, useState } from "react";

import {
  Button,
  Card,
  HeadingSmall,
  LabelSmall,
  Notification,
  ParagraphSmall,
  ParagraphXSmall,
  ProgressBar,
  Tag,
  type TagKind,
} from "./ui";

import { ApiError, getDesignThresholds, scoreDesign, type DesignScore } from "../api/client";

function describe(cause: unknown): string {
  if (cause instanceof ApiError) return cause.message;
  return cause instanceof Error ? cause.message : String(cause);
}

export function DesignBench(): React.JSX.Element {
  const [result, setResult] = useState<DesignScore | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // The full 9-category rubric, so "assessed" can be read as a fraction --
  // /score only returns the categories it actually measured.
  const [categoryCount, setCategoryCount] = useState<number | null>(null);
  const fileInput = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    getDesignThresholds()
      .then((thresholds) => {
        setCategoryCount(Object.keys(thresholds.categories).length);
      })
      .catch(() => {
        setCategoryCount(null);
      });
  }, []);

  const onFile = useCallback(async (file: File) => {
    setBusy(true);
    setError(null);
    setResult(null);
    setPreview((old) => {
      if (old) URL.revokeObjectURL(old);
      return URL.createObjectURL(file);
    });
    try {
      setResult(await scoreDesign(file, file.name.replace(/\.[^.]+$/, "")));
    } catch (cause) {
      setError(describe(cause));
    } finally {
      setBusy(false);
    }
  }, []);

  const measurements = (result?.measurements ?? {}) as Record<string, number | boolean | number[]>;
  const coverage =
    typeof measurements.print_coverage === "number" ? measurements.print_coverage : null;
  const assessed = result?.scoreCategories.length ?? 0;
  const failedGates = result?.hardGates.filter((gate) => gate.result === "fail").length ?? 0;
  const untestedGates =
    result?.hardGates.filter((gate) => gate.result === "not_tested").length ?? 0;
  const totalCategories = categoryCount ?? Math.max(assessed, 1);

  const statusTag = (status: string): TagKind =>
    status === "pass" ? "positive" : status === "fail" ? "negative" : "warning";

  return (
    <div className="flex flex-col gap-4">
      <div>
        <HeadingSmall className="mb-1">Design review</HeadingSmall>
        <ParagraphSmall className="text-ink/70">
          Measured against DESIGN_REVIEW_SCORECARD.md. Thresholds come from{" "}
          {result ? "the mined corpus" : "the design corpus"}, so “too many inks” means more than
          real production work uses.
        </ParagraphSmall>
      </div>

      <Card>
        <div className="flex flex-wrap items-center gap-3">
          <input
            ref={fileInput}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) void onFile(file);
              event.target.value = "";
            }}
          />
          <Button size="compact" disabled={busy} onClick={() => fileInput.current?.click()}>
            {result ? "Score another design" : "Choose a design image"}
          </Button>
          <ParagraphXSmall className="text-ink/70">
            JPEG, PNG or WebP. Worn or flat.
          </ParagraphXSmall>
        </div>
      </Card>

      {error && <Notification kind="negative">{error}</Notification>}

      {result && (
        <>
          <Notification kind="warning">
            {`${String(untestedGates)} gate(s) need a human, ${String(failedGates)} failed measurement. A design is never approved from one image -- see admin for the full review.`}
          </Notification>

          <div className="flex flex-wrap items-start gap-4">
            {preview && (
              <img
                src={preview}
                alt={result.designName}
                className="w-[220px] rounded-xl border border-ink/10"
              />
            )}

            <Card className="flex-1 basis-80">
              {/* No total or band shown here -- scoring and status are
                  decided by workflow.ts's evaluateReview, from the full set
                  of gates and categories a human review fills in. Showing a
                  partial score here would read as a verdict it has not
                  earned. */}
              <LabelSmall className="mb-1">
                {categoryCount !== null
                  ? `${String(assessed)} of ${String(categoryCount)} categories assessed`
                  : `${String(assessed)} categories assessed`}
              </LabelSmall>
              <ProgressBar value={(assessed / totalCategories) * 100} />
              <ParagraphXSmall className="mb-3 text-ink/70">
                Measurement rates what it can see. The remaining categories need a person, the
                brief, or the rest of the range.
              </ParagraphXSmall>

              <LabelSmall className="mb-1">Measured</LabelSmall>
              <ParagraphXSmall className="text-ink/70">
                {coverage !== null
                  ? `Print coverage ${(coverage * 100).toFixed(1)}%`
                  : "No print detected"}
                {typeof measurements.ink_colours === "number" &&
                  ` · ${String(measurements.ink_colours)} ink colours`}
                {measurements.light_on_dark !== undefined &&
                  ` · ${measurements.light_on_dark ? "light on dark" : "dark on light"}`}
              </ParagraphXSmall>
              <ParagraphXSmall className="text-ink/70">
                Thumbnail {measurements.thumbnail_survives ? "pass" : "fail"} · Blur{" "}
                {measurements.blur_survives ? "pass" : "fail"} · Greyscale{" "}
                {measurements.greyscale_survives ? "pass" : "fail"}
              </ParagraphXSmall>
            </Card>
          </div>

          <Card>
            <LabelSmall className="mb-2">Hard gates</LabelSmall>
            <div className="flex flex-col gap-1.5">
              {result.hardGates.map((gate) => (
                <div key={gate.id} className="flex flex-wrap items-baseline gap-2">
                  <Tag kind={statusTag(gate.result)}>
                    {gate.result === "not_tested" ? "needs a human" : gate.result}
                  </Tag>
                  <LabelSmall>{gate.label}</LabelSmall>
                  <ParagraphXSmall className="text-ink/70">{gate.evidence}</ParagraphXSmall>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <LabelSmall className="mb-2">Weighted categories measured</LabelSmall>
            {result.scoreCategories.length === 0 ? (
              <ParagraphXSmall className="text-ink/70">
                Nothing in this image supported a category rating.
              </ParagraphXSmall>
            ) : (
              result.scoreCategories.map((category) => {
                const belowFloor =
                  category.minimumRequired !== undefined &&
                  category.score < category.minimumRequired;
                return (
                  <div key={category.id} className="mb-1 flex items-baseline gap-2">
                    <ParagraphXSmall className="min-w-[190px]">{category.label}</ParagraphXSmall>
                    <ParagraphXSmall className="text-ink">
                      {category.score.toFixed(1)}/{category.maximum}
                      {belowFloor && ` — below floor of ${String(category.minimumRequired)}`}
                    </ParagraphXSmall>
                  </div>
                );
              })
            )}
          </Card>
        </>
      )}
    </div>
  );
}

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
import { useStyletron } from "baseui";
import { Button, SIZE } from "baseui/button";
import { Card, StyledBody } from "baseui/card";
import { Notification, KIND as NOTIFICATION_KIND } from "baseui/notification";
import { ProgressBar } from "baseui/progress-bar";
import { Tag, KIND as TAG_KIND } from "baseui/tag";
import { HeadingSmall, LabelSmall, ParagraphSmall, ParagraphXSmall } from "baseui/typography";

import { ApiError, getDesignThresholds, scoreDesign, type DesignScore } from "../api/client";

function describe(cause: unknown): string {
  if (cause instanceof ApiError) return cause.message;
  return cause instanceof Error ? cause.message : String(cause);
}

export function DesignBench(): React.JSX.Element {
  const [css, theme] = useStyletron();
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

  const statusTag = (status: string) =>
    status === "pass"
      ? TAG_KIND.positive
      : status === "fail"
        ? TAG_KIND.negative
        : TAG_KIND.warning;

  return (
    <div className={css({ display: "flex", flexDirection: "column", gap: "16px" })}>
      <div>
        <HeadingSmall marginTop={0} marginBottom="4px">
          Design review
        </HeadingSmall>
        <ParagraphSmall color={theme.colors.contentSecondary} marginTop={0}>
          Measured against DESIGN_REVIEW_SCORECARD.md. Thresholds come from{" "}
          {result ? "the mined corpus" : "the design corpus"}, so “too many inks” means more than
          real production work uses.
        </ParagraphSmall>
      </div>

      <Card>
        <StyledBody>
          <div
            className={css({
              display: "flex",
              gap: "12px",
              alignItems: "center",
              flexWrap: "wrap",
            })}
          >
            <input
              ref={fileInput}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className={css({ display: "none" })}
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) void onFile(file);
                event.target.value = "";
              }}
            />
            <Button size={SIZE.compact} isLoading={busy} onClick={() => fileInput.current?.click()}>
              {result ? "Score another design" : "Choose a design image"}
            </Button>
            <ParagraphXSmall color={theme.colors.contentSecondary} margin={0}>
              JPEG, PNG or WebP. Worn or flat.
            </ParagraphXSmall>
          </div>
        </StyledBody>
      </Card>

      {error && (
        <Notification
          kind={NOTIFICATION_KIND.negative}
          overrides={{ Body: { style: { width: "auto" } } }}
        >
          {error}
        </Notification>
      )}

      {result && (
        <>
          <Notification
            kind={NOTIFICATION_KIND.warning}
            overrides={{ Body: { style: { width: "auto" } } }}
          >
            {`${String(untestedGates)} gate(s) need a human, ${String(failedGates)} failed measurement. A design is never approved from one image -- see admin for the full review.`}
          </Notification>

          <div
            className={css({
              display: "flex",
              gap: "16px",
              flexWrap: "wrap",
              alignItems: "flex-start",
            })}
          >
            {preview && (
              <img
                src={preview}
                alt={result.designName}
                className={css({
                  width: "220px",
                  borderRadius: "12px",
                  border: `1px solid ${theme.colors.borderOpaque}`,
                })}
              />
            )}

            <Card overrides={{ Root: { style: { flex: "1 1 320px" } } }}>
              <StyledBody>
                {/* No total or band shown here -- scoring and status are
                    decided by workflow.ts's evaluateReview, from the full set
                    of gates and categories a human review fills in. Showing a
                    partial score here would read as a verdict it has not
                    earned. */}
                <LabelSmall marginBottom="4px">
                  {categoryCount !== null
                    ? `${String(assessed)} of ${String(categoryCount)} categories assessed`
                    : `${String(assessed)} categories assessed`}
                </LabelSmall>
                <ProgressBar
                  value={assessed}
                  maxValue={categoryCount ?? Math.max(assessed, 1)}
                  overrides={{
                    BarProgress: { style: { backgroundColor: theme.colors.contentPrimary } },
                  }}
                />
                <ParagraphXSmall color={theme.colors.contentSecondary} marginBottom="12px">
                  Measurement rates what it can see. The remaining categories need a person, the
                  brief, or the rest of the range.
                </ParagraphXSmall>

                <LabelSmall marginBottom="4px">Measured</LabelSmall>
                <ParagraphXSmall margin={0} color={theme.colors.contentSecondary}>
                  {coverage !== null
                    ? `Print coverage ${(coverage * 100).toFixed(1)}%`
                    : "No print detected"}
                  {typeof measurements.ink_colours === "number" &&
                    ` · ${String(measurements.ink_colours)} ink colours`}
                  {measurements.light_on_dark !== undefined &&
                    ` · ${measurements.light_on_dark ? "light on dark" : "dark on light"}`}
                </ParagraphXSmall>
                <ParagraphXSmall margin={0} color={theme.colors.contentSecondary}>
                  Thumbnail {measurements.thumbnail_survives ? "pass" : "fail"} · Blur{" "}
                  {measurements.blur_survives ? "pass" : "fail"} · Greyscale{" "}
                  {measurements.greyscale_survives ? "pass" : "fail"}
                </ParagraphXSmall>
              </StyledBody>
            </Card>
          </div>

          <Card>
            <StyledBody>
              <LabelSmall marginBottom="8px">Hard gates</LabelSmall>
              <div className={css({ display: "flex", flexDirection: "column", gap: "6px" })}>
                {result.hardGates.map((gate) => (
                  <div
                    key={gate.id}
                    className={css({
                      display: "flex",
                      gap: "8px",
                      alignItems: "baseline",
                      flexWrap: "wrap",
                    })}
                  >
                    <Tag
                      closeable={false}
                      kind={statusTag(gate.result)}
                      overrides={{ Root: { style: { marginTop: 0, marginBottom: 0 } } }}
                    >
                      {gate.result === "not_tested" ? "needs a human" : gate.result}
                    </Tag>
                    <LabelSmall margin={0}>{gate.label}</LabelSmall>
                    <ParagraphXSmall margin={0} color={theme.colors.contentSecondary}>
                      {gate.evidence}
                    </ParagraphXSmall>
                  </div>
                ))}
              </div>
            </StyledBody>
          </Card>

          <Card>
            <StyledBody>
              <LabelSmall marginBottom="8px">Weighted categories measured</LabelSmall>
              {result.scoreCategories.length === 0 ? (
                <ParagraphXSmall margin={0} color={theme.colors.contentSecondary}>
                  Nothing in this image supported a category rating.
                </ParagraphXSmall>
              ) : (
                result.scoreCategories.map((category) => {
                  const belowFloor =
                    category.minimumRequired !== undefined &&
                    category.score < category.minimumRequired;
                  return (
                    <div
                      key={category.id}
                      className={css({
                        display: "flex",
                        gap: "8px",
                        alignItems: "baseline",
                        marginBottom: "4px",
                      })}
                    >
                      <ParagraphXSmall margin={0} className={css({ minWidth: "190px" })}>
                        {category.label}
                      </ParagraphXSmall>
                      <ParagraphXSmall margin={0} color={theme.colors.contentPrimary}>
                        {category.score.toFixed(1)}/{category.maximum}
                        {belowFloor && ` — below floor of ${String(category.minimumRequired)}`}
                      </ParagraphXSmall>
                    </div>
                  );
                })
              )}
            </StyledBody>
          </Card>
        </>
      )}
    </div>
  );
}

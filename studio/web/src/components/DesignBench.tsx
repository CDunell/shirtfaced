/**
 * Scoring a design against the review scorecard.
 *
 * Drop a design in and it is measured -- print coverage, ink count, placement,
 * and the scorecard's own thumbnail, blur and greyscale tests -- then scored
 * through the twelve hard gates and nine weighted categories.
 *
 * The result always blocks, and the screen says so plainly rather than showing a
 * number that looks like a verdict. Measurement fills the gates it can answer
 * honestly and leaves the rest untested; an untested gate blocks release exactly
 * as a failed one does. What this produces is the start of a review, with the
 * measurable half already done, not a decision.
 */

import { useCallback, useRef, useState } from "react";
import { useStyletron } from "baseui";
import { Button, SIZE } from "baseui/button";
import { Card, StyledBody } from "baseui/card";
import { Notification, KIND as NOTIFICATION_KIND } from "baseui/notification";
import { ProgressBar } from "baseui/progress-bar";
import { Tag, KIND as TAG_KIND } from "baseui/tag";
import { HeadingSmall, LabelSmall, ParagraphSmall, ParagraphXSmall } from "baseui/typography";

import { ApiError, scoreDesign, type DesignScore } from "../api/client";

function describe(cause: unknown): string {
  if (cause instanceof ApiError) return cause.message;
  return cause instanceof Error ? cause.message : String(cause);
}

/** Turn a snake_case gate or category name into something readable. */
function humanise(value: string): string {
  return value.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());
}

const BAND_LABEL: Record<string, string> = {
  release_candidate: "Release candidate",
  strong_revise_selectively: "Strong — revise selectively",
  rework: "Rework",
  reject_or_rebuild: "Reject or rebuild",
};

export function DesignBench(): React.JSX.Element {
  const [css, theme] = useStyletron();
  const [result, setResult] = useState<DesignScore | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement | null>(null);

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
  const coverage = typeof measurements.print_coverage === "number" ? measurements.print_coverage : null;
  const assessed = result?.categories.filter((category) => category.rating > 0).length ?? 0;

  const statusTag = (status: string) =>
    status === "pass" ? TAG_KIND.positive : status === "fail" ? TAG_KIND.negative : TAG_KIND.warning;

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
          <div className={css({ display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" })}>
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
        <Notification kind={NOTIFICATION_KIND.negative} overrides={{ Body: { style: { width: "auto" } } }}>
          {error}
        </Notification>
      )}

      {result && (
        <>
          <Notification
            kind={result.blocked ? NOTIFICATION_KIND.warning : NOTIFICATION_KIND.positive}
            overrides={{ Body: { style: { width: "auto" } } }}
          >
            {result.blocked
              ? `Blocked — ${String(result.untested_gates.length)} gate(s) need a human, ${String(result.failed_gates.length)} failed. A design is never approved from one image.`
              : "No blocking gates from measurement alone."}
          </Notification>

          <div className={css({ display: "flex", gap: "16px", flexWrap: "wrap", alignItems: "flex-start" })}>
            {preview && (
              <img
                src={preview}
                alt={result.design_name}
                className={css({
                  width: "220px",
                  borderRadius: "12px",
                  border: `1px solid ${theme.colors.borderOpaque}`,
                })}
              />
            )}

            <Card overrides={{ Root: { style: { flex: "1 1 320px" } } }}>
              <StyledBody>
                {/* The band is deliberately withheld while most categories are
                    unrated. A design that has only been measured scores single
                    digits out of 100 and would read as "reject or rebuild" --
                    a verdict on work nobody has reviewed yet. Showing the
                    assessed fraction instead is the honest version. */}
                {assessed < result.categories.length ? (
                  <>
                    <LabelSmall marginBottom="4px">
                      Not yet scorable — {assessed} of {result.categories.length} categories assessed
                    </LabelSmall>
                    <ProgressBar
                      value={assessed}
                      maxValue={result.categories.length}
                      overrides={{ BarProgress: { style: { backgroundColor: theme.colors.contentPrimary } } }}
                    />
                    <ParagraphXSmall color={theme.colors.contentSecondary} marginBottom="12px">
                      Measurement rates what it can see. The remaining categories need a person, the
                      brief, or the rest of the range — no total or band is shown until they are in,
                      because a partial score reads as a verdict it has not earned.
                    </ParagraphXSmall>
                  </>
                ) : (
                  <>
                    <LabelSmall marginBottom="4px">
                      {result.total_score} / {result.max_total_score} —{" "}
                      {BAND_LABEL[result.band] ?? result.band}
                    </LabelSmall>
                    <ProgressBar
                      value={result.total_score}
                      maxValue={result.max_total_score}
                      overrides={{ BarProgress: { style: { backgroundColor: theme.colors.contentPrimary } } }}
                    />
                  </>
                )}

                <LabelSmall marginBottom="4px">Measured</LabelSmall>
                <ParagraphXSmall margin={0} color={theme.colors.contentSecondary}>
                  {coverage !== null ? `Print coverage ${(coverage * 100).toFixed(1)}%` : "No print detected"}
                  {typeof measurements.ink_colours === "number" && ` · ${String(measurements.ink_colours)} ink colours`}
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
                {result.gates.map((gate) => (
                  <div
                    key={gate.gate}
                    className={css({ display: "flex", gap: "8px", alignItems: "baseline", flexWrap: "wrap" })}
                  >
                    <Tag closeable={false} kind={statusTag(gate.status)} overrides={{ Root: { style: { marginTop: 0, marginBottom: 0 } } }}>
                      {gate.status === "not_tested" ? "needs a human" : gate.status}
                    </Tag>
                    <LabelSmall margin={0}>{humanise(gate.gate)}</LabelSmall>
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
              <LabelSmall marginBottom="8px">Weighted categories</LabelSmall>
              {result.categories.map((category) => (
                <div
                  key={category.category}
                  className={css({ display: "flex", gap: "8px", alignItems: "baseline", marginBottom: "4px" })}
                >
                  <ParagraphXSmall margin={0} className={css({ minWidth: "190px" })}>
                    {humanise(category.category)}
                  </ParagraphXSmall>
                  <ParagraphXSmall
                    margin={0}
                    color={category.rating === 0 ? theme.colors.contentSecondary : theme.colors.contentPrimary}
                  >
                    {category.rating}/5 → {category.points.toFixed(1)}/{category.max_points}
                    {category.rating === 0 && " (not assessed)"}
                    {category.below_floor && ` — below floor of ${String(category.floor)}`}
                  </ParagraphXSmall>
                </div>
              ))}
            </StyledBody>
          </Card>
        </>
      )}
    </div>
  );
}

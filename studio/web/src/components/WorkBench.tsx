/**
 * Work — what is outstanding, and the one thing to do to each of it.
 *
 * Phase 3 of DESIGN_FLOW_PLAN.md, and the plan's governing rule made literal:
 * at every point there is exactly one obvious next action, and following the
 * chain requires no knowledge of which screen owns what.
 *
 * So each row is a sentence and a button, and the button goes straight to the
 * place the sentence describes. Nothing else is on it. It is deliberately not a
 * dashboard: no counts, no charts, no status tiles. A tile saying "4 awaiting
 * decision" tells you the size of a problem; a row saying what to do about one
 * of them lets you do it.
 *
 * The sentences are the server's — `next_action.py`, one copy of each phrasing
 * — so Work and the attempt screen cannot describe the same row differently.
 *
 * The plan corrected in passing: it said "Work replaces the Dashboard". Phase 2a
 * put the Dashboard on the world side, where it belongs, so Work does not
 * replace it — it is the product tool's own front door, and the world Dashboard
 * stays as world.
 */

import { useCallback, useEffect, useState } from "react";
import { useStyletron } from "baseui";
import { Button, KIND as BUTTON_KIND, SIZE } from "baseui/button";
import { Notification, KIND as NOTIFICATION_KIND } from "baseui/notification";
import { ParagraphSmall, ParagraphXSmall } from "baseui/typography";

import { ApiError } from "../api/client";
import { fetchWork, type WorkItem, type WorkStage } from "../api/concepts";
import { PageTitle, SectionTitle } from "./chrome";
import { INK, LIME, PAPER } from "../tokens";

function describe(cause: unknown): string {
  if (cause instanceof ApiError) return cause.message;
  return cause instanceof Error ? cause.message : String(cause);
}

/** What each stage is called, and what the button that acts on it says.
 *
 * The verb matters more than the noun: "Judge it" is a thing to do, "awaiting
 * decision" is a thing to be. */
const STAGES: Partial<Record<WorkStage, { label: string; action: string }>> = {
  awaiting_decision: { label: "Waiting on you", action: "Judge it" },
  review_open: { label: "Review open", action: "Answer the scorecard" },
  needs_artwork: { label: "Needs artwork", action: "Open the brief" },
  needs_brief: { label: "Needs a brief", action: "Write the brief" },
  approved_unversioned: { label: "Approved", action: "Record the version" },
  ready_to_print: { label: "Ready to print", action: "Open it" },
  unstarted: { label: "Not started", action: "Start it" },
  settled: { label: "Settled", action: "Open it" },
};

/** A stage this build has never heard of still has to render.
 *
 * The server owns the stage vocabulary and can add to it, and this file cannot
 * be deployed in the same instant. Phase 4 added `needs_brief` on the server
 * while this map still held Phase 3's seven; `STAGES[stage].label` threw, and
 * because Work is the default view **the whole application rendered blank in
 * production** while the API, the smoke chain and CI all stayed green.
 *
 * So the lookup is total. An unknown stage shows the row and its sentence --
 * which is the part that actually tells somebody what to do -- rather than
 * taking the page down. */
function stageOf(stage: WorkStage): { label: string; action: string } {
  return STAGES[stage] ?? { label: stage.replace(/_/g, " "), action: "Open it" };
}

function number3(value: number): string {
  return `#${String(value).padStart(3, "0")}`;
}

export interface WorkBenchProps {
  /** Open this item where it can be worked on. Work never edits anything
   * itself; it is a way in, not a second place to do the job. */
  onOpen: (item: WorkItem) => void;
}

export function WorkBench({ onOpen }: WorkBenchProps): React.JSX.Element {
  const [css, theme] = useStyletron();
  const [items, setItems] = useState<WorkItem[]>([]);
  const [showSettled, setShowSettled] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  const refresh = useCallback(async () => {
    try {
      setItems(await fetchWork(showSettled));
      setError(null);
    } catch (cause) {
      setError(describe(cause));
    } finally {
      setLoaded(true);
    }
  }, [showSettled]);

  useEffect(() => {
    const timer = setTimeout(() => {
      void refresh();
    }, 0);
    return () => {
      clearTimeout(timer);
    };
  }, [refresh]);

  const first = items[0];

  return (
    <>
      <PageTitle meta={loaded ? `${String(items.length)} outstanding` : undefined}>Work</PageTitle>
      <ParagraphSmall color={theme.colors.contentSecondary} marginTop={0}>
        Everything being made, most-blocked first. Each row says what to do next and the button goes
        straight there.
      </ParagraphSmall>

      {error ? (
        <Notification
          kind={NOTIFICATION_KIND.negative}
          overrides={{ Body: { style: { width: "auto" } } }}
        >
          {error}
        </Notification>
      ) : null}

      {/* The top of the list, said once and loudly. If only one thing gets
          read on this page, it should be the thing to do now. */}
      {first ? (
        <section
          className={css({
            backgroundColor: INK,
            color: PAPER,
            borderRadius: "20px",
            padding: "24px",
            marginBottom: theme.sizing.scale700,
          })}
        >
          <span
            className={css({
              display: "block",
              fontSize: "11px",
              fontWeight: 700,
              letterSpacing: "0.12em",
              textTransform: "uppercase",
              color: LIME,
              marginBottom: "10px",
            })}
          >
            Start here
          </span>
          <h2
            className={`display ${css({
              fontSize: "clamp(26px, 5vw, 36px)",
              margin: "0 0 10px",
              color: "inherit",
            })}`}
          >
            {number3(first.external_number)} {first.title}
          </h2>
          <p
            className={css({
              margin: "0 0 16px",
              fontSize: "15px",
              lineHeight: 1.55,
              opacity: 0.8,
              maxWidth: "640px",
            })}
          >
            {first.next_action}
          </p>
          <Button
            size={SIZE.compact}
            onClick={() => {
              onOpen(first);
            }}
          >
            {stageOf(first.stage).action}
          </Button>
        </section>
      ) : null}

      <div
        className={css({
          display: "flex",
          alignItems: "center",
          gap: "12px",
          flexWrap: "wrap",
        })}
      >
        <SectionTitle count={items.length}>Outstanding</SectionTitle>
        <button
          type="button"
          aria-pressed={showSettled}
          onClick={() => {
            setShowSettled((previous) => !previous);
          }}
          className={`press ${css({
            appearance: "none",
            border: "none",
            cursor: "pointer",
            fontFamily: "inherit",
            fontSize: "12px",
            fontWeight: 700,
            letterSpacing: "0.04em",
            textTransform: "uppercase",
            borderRadius: "999px",
            padding: "6px 12px",
            backgroundColor: showSettled ? theme.colors.contentPrimary : "transparent",
            color: showSettled ? theme.colors.backgroundPrimary : theme.colors.contentSecondary,
            ":hover": showSettled ? {} : { backgroundColor: theme.colors.backgroundSecondary },
          })}`}
        >
          {showSettled ? "Hiding nothing" : "Show settled"}
        </button>
      </div>

      {loaded && items.length === 0 ? (
        <ParagraphSmall color={theme.colors.contentSecondary}>
          Nothing is outstanding. Every concept is either finished or not yet started.
        </ParagraphSmall>
      ) : null}

      <div
        className={css({
          border: `1px solid ${theme.colors.backgroundSecondary}`,
          borderRadius: "16px",
          overflow: "hidden",
        })}
      >
        {items.map((item, index) => (
          <div
            key={item.concept_id}
            data-testid="work-row"
            className={css({
              display: "flex",
              alignItems: "center",
              gap: "14px",
              flexWrap: "wrap",
              padding: "14px 16px",
              borderTop: index === 0 ? "none" : `1px solid ${theme.colors.backgroundSecondary}`,
            })}
          >
            <span
              className={css({
                fontVariantNumeric: "tabular-nums",
                fontSize: "12px",
                fontWeight: 600,
                color: theme.colors.contentTertiary,
                minWidth: "42px",
              })}
            >
              {number3(item.external_number)}
            </span>

            <div className={css({ flex: "1 1 320px", minWidth: "240px" })}>
              <div
                className={css({
                  display: "flex",
                  alignItems: "baseline",
                  gap: "8px",
                  flexWrap: "wrap",
                })}
              >
                <span
                  className={css({
                    fontSize: "14px",
                    fontWeight: 700,
                    color: theme.colors.contentPrimary,
                  })}
                >
                  {item.title}
                </span>
                <span
                  className={css({
                    fontSize: "11px",
                    fontWeight: 700,
                    letterSpacing: "0.06em",
                    textTransform: "uppercase",
                    color: theme.colors.contentTertiary,
                  })}
                >
                  {stageOf(item.stage).label}
                  {item.percentage === null ? "" : ` · ${item.percentage.toFixed(0)}/100`}
                  {item.attempt_number === null ? "" : ` · attempt ${String(item.attempt_number)}`}
                </span>
              </div>
              <ParagraphXSmall
                marginTop="2px"
                marginBottom={0}
                color={theme.colors.contentSecondary}
              >
                {item.next_action}
              </ParagraphXSmall>
            </div>

            <Button
              size={SIZE.mini}
              kind={index === 0 ? BUTTON_KIND.primary : BUTTON_KIND.secondary}
              onClick={() => {
                onOpen(item);
              }}
            >
              {stageOf(item.stage).action}
            </Button>
          </div>
        ))}
      </div>
    </>
  );
}

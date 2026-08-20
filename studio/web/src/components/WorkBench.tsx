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
import { Button, cx, Notification, ParagraphSmall, ParagraphXSmall } from "./ui";

import { ApiError } from "../api/client";
import { fetchWork, type WorkItem, type WorkStage } from "../api/concepts";
import { PageTitle, SectionTitle } from "./chrome";

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
      <ParagraphSmall className="mt-0 text-ink/70">
        Everything being made, most-blocked first. Each row says what to do next and the button goes
        straight there.
      </ParagraphSmall>

      {error ? <Notification kind="negative">{error}</Notification> : null}

      {/* The top of the list, said once and loudly. If only one thing gets
          read on this page, it should be the thing to do now. */}
      {first ? (
        <section className="mb-7 rounded-[20px] bg-ink p-6 text-paper">
          <span className="mb-[10px] block text-[11px] font-bold tracking-[0.12em] text-lime uppercase">
            Start here
          </span>
          <h2 className="display m-0 mb-[10px] text-[clamp(26px,5vw,36px)] text-inherit">
            {number3(first.external_number)} {first.title}
          </h2>
          <p className="m-0 mb-4 max-w-[640px] text-[15px] leading-[1.55] opacity-80">
            {first.next_action}
          </p>
          <Button
            size="compact"
            onClick={() => {
              onOpen(first);
            }}
          >
            {stageOf(first.stage).action}
          </Button>
        </section>
      ) : null}

      <div className="flex flex-wrap items-center gap-3">
        <SectionTitle count={items.length}>Outstanding</SectionTitle>
        <button
          type="button"
          aria-pressed={showSettled}
          onClick={() => {
            setShowSettled((previous) => !previous);
          }}
          className={cx(
            "press appearance-none cursor-pointer rounded-full border-none px-3 py-1.5 font-sans text-[12px] font-bold tracking-[0.04em] uppercase",
            showSettled ? "bg-ink text-paper" : "bg-transparent text-ink/70 hover:bg-paper-2",
          )}
        >
          {showSettled ? "Hiding nothing" : "Show settled"}
        </button>
      </div>

      {loaded && items.length === 0 ? (
        <ParagraphSmall className="text-ink/70">
          Nothing is outstanding. Every concept is either finished or not yet started.
        </ParagraphSmall>
      ) : null}

      <div className="overflow-hidden rounded-2xl border border-paper-2">
        {items.map((item, index) => (
          <div
            key={item.concept_id}
            data-testid="work-row"
            className={cx(
              "flex flex-wrap items-center gap-3.5 px-4 py-3.5",
              index !== 0 && "border-t border-paper-2",
            )}
          >
            <span className="min-w-[42px] text-[12px] font-semibold text-ink/50 tabular-nums">
              {number3(item.external_number)}
            </span>

            <div className="min-w-[240px] flex-[1_1_320px]">
              <div className="flex flex-wrap items-baseline gap-2">
                <span className="text-[14px] font-bold text-ink">{item.title}</span>
                <span className="text-[11px] font-bold tracking-[0.06em] text-ink/50 uppercase">
                  {stageOf(item.stage).label}
                  {item.percentage === null ? "" : ` · ${item.percentage.toFixed(0)}/100`}
                  {item.attempt_number === null ? "" : ` · attempt ${String(item.attempt_number)}`}
                </span>
              </div>
              <ParagraphXSmall className="mt-0.5 mb-0 text-ink/70">
                {item.next_action}
              </ParagraphXSmall>
            </div>

            <Button
              size="compact"
              variant={index === 0 ? "primary" : "secondary"}
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

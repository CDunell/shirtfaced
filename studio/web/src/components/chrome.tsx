/**
 * The page furniture every bench shares.
 *
 * Rebuilt on Tailwind, off Base Web/styletron -- see docs/ADMIN_STUDIO_UI_OVERHAUL_PLAN.md
 * Phase 0. Every exported signature here is unchanged from the Base Web version
 * so consuming benches don't need to change anything until their own migration
 * turn.
 *
 * Three rules, all taken from the storefront rather than invented:
 *
 * - Pages open with a display block, not a component-library heading. The
 *   site shouts its section titles and so does the tool.
 * - Sections are marked by quiet uppercase overlines, so the display type
 *   stays rare enough to mean something.
 * - Accents mark emphasis and never decorate. A chip is only coloured when
 *   its state is worth colouring, and the default state of anything is
 *   unmarked -- 260 grey "backlog" chips said nothing 260 times.
 */

import { useCallback, useEffect, useState, type ReactNode } from "react";

import { cx, Tag, type TagKind } from "./ui";

export function PageTitle({
  children,
  meta,
}: {
  children: ReactNode;
  meta?: ReactNode;
}): React.JSX.Element {
  return (
    <div className="mb-6 flex flex-wrap items-baseline justify-between gap-3">
      <h1 className="display text-[clamp(34px,6vw,44px)] text-ink">{children}</h1>
      {meta ? (
        <span className="text-[13px] font-semibold tracking-wide text-ink/50 uppercase">
          {meta}
        </span>
      ) : null}
    </div>
  );
}

export function SectionTitle({
  children,
  count,
}: {
  children: ReactNode;
  count?: number;
}): React.JSX.Element {
  return (
    <h2 className="mt-8 mb-2 flex items-center gap-2 text-[13px] font-bold tracking-wide text-ink uppercase">
      {children}
      {count !== undefined ? <span className="font-semibold text-ink/50">{count}</span> : null}
    </h2>
  );
}

/**
 * Accent backgrounds carry ink text in both themes -- lime, coral and cream
 * read the same on paper and on ink, which is why the site uses them as its
 * only colour. Neutral states stay theme-coloured and quiet.
 */
const CHIP_KIND: Record<string, TagKind> = {
  approved: "positive",
  rejected: "negative",
  retired: "negative",
  failed: "negative",
  held: "warning",
  variation_requested: "warning",
};

export function StatusChip({ status }: { status: string }): React.JSX.Element {
  return <Tag kind={CHIP_KIND[status] ?? "neutral"}>{status.replace(/_/g, " ")}</Tag>;
}

const iconButtonClass =
  "press inline-flex items-center gap-1.5 rounded-[10px] border border-ink/15 px-2 py-1 font-sans text-[12px] font-semibold";

/**
 * Copy a block of text, and say that it worked.
 *
 * Selecting a long prompt by hand on a phone is miserable, and the manual
 * research path is built entirely on moving prompts into another window --
 * so this is the gesture that path depends on rather than a convenience.
 *
 * Falls back silently where the clipboard API is absent: the text stays
 * selectable, and claiming a copy that did not happen is worse than saying
 * nothing.
 */
export function CopyButton({
  text,
  label = "Copy",
}: {
  text: string;
  label?: string;
}): React.JSX.Element {
  const [copied, setCopied] = useState(false);

  const copy = useCallback(() => {
    void navigator.clipboard.writeText(text).then(
      () => {
        setCopied(true);
      },
      () => {
        setCopied(false);
      },
    );
  }, [text]);

  useEffect(() => {
    if (!copied) return undefined;
    const timer = setTimeout(() => {
      setCopied(false);
    }, 2000);
    return () => {
      clearTimeout(timer);
    };
  }, [copied]);

  return (
    <button
      type="button"
      onClick={copy}
      aria-label={copied ? "Copied" : `Copy ${label}`}
      title={copied ? "Copied" : `Copy ${label}`}
      className={cx(iconButtonClass, copied ? "bg-ink text-paper" : "bg-transparent text-ink")}
    >
      {copied ? (
        <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
          <path
            d="M20 6 9 17l-5-5"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      ) : (
        <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
          <rect x="9" y="9" width="11" height="11" rx="2" fill="none" stroke="currentColor" strokeWidth="2" />
          <path
            d="M5 15V5a2 2 0 0 1 2-2h10"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          />
        </svg>
      )}
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

/**
 * Fill a field from the clipboard.
 *
 * The counterpart to CopyButton, and the other half of the manual research
 * loop: a prompt goes out to another window, concepts come back. Pasting a
 * long JSON blob into a textarea on a phone is the same misery as selecting
 * one, in reverse.
 *
 * Reading the clipboard needs permission and the browser may refuse. On
 * refusal this reports it rather than failing quietly, because a paste button
 * that silently does nothing is worse than no button -- the field is still
 * there to paste into by hand.
 */
export function PasteButton({
  onPaste,
  label = "Paste",
}: {
  onPaste: (text: string) => void;
  label?: string;
}): React.JSX.Element {
  const [state, setState] = useState<"idle" | "done" | "refused">("idle");

  const paste = useCallback(() => {
    void navigator.clipboard.readText().then(
      (text) => {
        onPaste(text);
        setState("done");
      },
      () => {
        setState("refused");
      },
    );
  }, [onPaste]);

  useEffect(() => {
    // A success can fade; a refusal must not. Clearing "Blocked" after a couple
    // of seconds leaves the reader with an empty field, a button that appears
    // to have worked, and nothing to act on.
    if (state !== "done") return undefined;
    const timer = setTimeout(() => {
      setState("idle");
    }, 2500);
    return () => {
      clearTimeout(timer);
    };
  }, [state]);

  const caption = state === "done" ? "Pasted" : state === "refused" ? "Blocked" : label;

  return (
    <button
      type="button"
      onClick={paste}
      aria-label={caption}
      title={
        state === "refused"
          ? "The browser refused clipboard access — paste into the field instead"
          : caption
      }
      className={cx(iconButtonClass, state === "done" ? "bg-ink text-paper" : "bg-transparent text-ink")}
    >
      <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
        <rect x="8" y="4" width="8" height="4" rx="1" fill="none" stroke="currentColor" strokeWidth="2" />
        <path
          d="M8 6H6a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-2"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
        />
      </svg>
      {caption}
    </button>
  );
}

/** A section that is closed until asked for, and mounts nothing until it opens.
 *
 * Phase 5 folds Compose and Score into Designs. Rendering both eagerly would
 * make one screen fetch three benches' worth of data to show a backlog, so the
 * children are not constructed until the panel is open — which is also why this
 * takes a render function rather than elements.
 */
export function Disclosure({
  label,
  blurb,
  children,
}: {
  label: string;
  blurb: string;
  children: () => ReactNode;
}): React.JSX.Element {
  const [open, setOpen] = useState(false);
  return (
    <section className="mt-6 overflow-hidden rounded-2xl border border-paper-2">
      <button
        type="button"
        aria-expanded={open}
        onClick={() => {
          setOpen((previous) => !previous);
        }}
        className={cx(
          "flex w-full flex-wrap items-baseline gap-2.5 px-4 py-3.5 text-left font-sans",
          open ? "bg-paper-2" : "bg-transparent hover:bg-paper-2",
        )}
      >
        <span className="text-[13px] font-bold tracking-wide text-ink uppercase">
          {open ? "−" : "+"} {label}
        </span>
        <span className="text-[12px] text-ink/50">{blurb}</span>
      </button>
      {open ? <div className="p-4">{children()}</div> : null}
    </section>
  );
}

/**
 * The page furniture every bench shares.
 *
 * The brand sheet gave Studio its palette and type; this gives it a voice.
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
import { useStyletron } from "baseui";

import { CORAL, CREAM, LIME } from "../tokens";

export function PageTitle({
  children,
  meta,
}: {
  children: ReactNode;
  meta?: ReactNode;
}): React.JSX.Element {
  const [css, theme] = useStyletron();
  return (
    <div
      className={css({
        display: "flex",
        alignItems: "baseline",
        justifyContent: "space-between",
        gap: "12px",
        flexWrap: "wrap",
        marginBottom: theme.sizing.scale600,
      })}
    >
      <h1
        className={`display ${css({
          fontSize: "clamp(34px, 6vw, 44px)",
          margin: 0,
          color: theme.colors.contentPrimary,
        })}`}
      >
        {children}
      </h1>
      {meta ? (
        <span
          className={css({
            fontSize: "13px",
            fontWeight: 600,
            letterSpacing: "0.04em",
            textTransform: "uppercase",
            color: theme.colors.contentTertiary,
          })}
        >
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
  const [css, theme] = useStyletron();
  return (
    <h2
      className={css({
        display: "flex",
        alignItems: "center",
        gap: "8px",
        fontSize: "13px",
        fontWeight: 700,
        letterSpacing: "0.08em",
        textTransform: "uppercase",
        color: theme.colors.contentPrimary,
        margin: `${theme.sizing.scale800} 0 ${theme.sizing.scale400}`,
      })}
    >
      {children}
      {count !== undefined ? (
        <span className={css({ color: theme.colors.contentTertiary, fontWeight: 600 })}>
          {count}
        </span>
      ) : null}
    </h2>
  );
}

/**
 * Accent backgrounds carry ink text in both themes -- lime, coral and cream
 * read the same on paper and on ink, which is why the site uses them as its
 * only colour. Neutral states stay theme-coloured and quiet.
 */
const CHIP_ACCENTS: Record<string, string> = {
  approved: LIME,
  rejected: CORAL,
  retired: CORAL,
  failed: CORAL,
  held: CREAM,
  variation_requested: CREAM,
};

export function StatusChip({ status }: { status: string }): React.JSX.Element {
  const [css, theme] = useStyletron();
  const accent = CHIP_ACCENTS[status];
  return (
    <span
      className={css({
        display: "inline-block",
        fontSize: "11px",
        fontWeight: 700,
        letterSpacing: "0.06em",
        textTransform: "uppercase",
        whiteSpace: "nowrap",
        borderRadius: "8px",
        paddingTop: "3px",
        paddingBottom: "3px",
        paddingLeft: "8px",
        paddingRight: "8px",
        backgroundColor: accent ?? theme.colors.backgroundSecondary,
        color: accent ? "#0d0d0d" : theme.colors.contentSecondary,
      })}
    >
      {status.replace(/_/g, " ")}
    </span>
  );
}

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
  const [css, theme] = useStyletron();
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
      className={css({
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        appearance: "none",
        cursor: "pointer",
        border: `1px solid ${theme.colors.borderOpaque}`,
        borderRadius: "8px",
        padding: "4px 8px",
        fontFamily: "inherit",
        fontSize: "12px",
        fontWeight: 600,
        backgroundColor: copied ? theme.colors.contentPrimary : "transparent",
        color: copied ? theme.colors.backgroundPrimary : theme.colors.contentPrimary,
      })}
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
          <rect
            x="9"
            y="9"
            width="11"
            height="11"
            rx="2"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          />
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
  const [css, theme] = useStyletron();
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
    if (state === "idle") return undefined;
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
      className={css({
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        appearance: "none",
        cursor: "pointer",
        border: `1px solid ${theme.colors.borderOpaque}`,
        borderRadius: "8px",
        padding: "4px 8px",
        fontFamily: "inherit",
        fontSize: "12px",
        fontWeight: 600,
        backgroundColor: state === "done" ? theme.colors.contentPrimary : "transparent",
        color: state === "done" ? theme.colors.backgroundPrimary : theme.colors.contentPrimary,
      })}
    >
      <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
        <rect
          x="8"
          y="4"
          width="8"
          height="4"
          rx="1"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        />
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

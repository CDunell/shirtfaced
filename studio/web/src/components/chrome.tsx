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

import type { ReactNode } from "react";
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

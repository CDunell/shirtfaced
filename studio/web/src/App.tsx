/** Application shell. */
import { useState } from "react";
import { useStyletron } from "baseui";
import { ParagraphMedium } from "baseui/typography";
import { ComposeBench } from "./components/ComposeBench";
import { WorkBench } from "./components/WorkBench";
import { DesignBench } from "./components/DesignBench";
import { DesignsBench } from "./components/DesignsBench";
import { EmailBench } from "./components/EmailBench";
import { PrintBench } from "./components/PrintBench";
import { VintageEvidenceBench } from "./components/VintageEvidenceBench";
import { VintageResearchBench } from "./components/VintageResearchBench";
import { PromptWorkbench } from "./components/PromptWorkbench";
import { ServiceStatus } from "./components/ServiceStatus";
import { SocialBench } from "./components/SocialBench";
import { WorldPage } from "./components/WorldPage";
import type { WorkItem } from "./api/concepts";
import type { ThemeName } from "./theme";
export interface AppProps {
  themeName: ThemeName;
  onToggleTheme: () => void;
}
type View =
  | "work"
  | "prompts"
  | "print"
  | "compose"
  | "concepts"
  | "design"
  | "evidence"
  | "research"
  | "social"
  | "email"
  | "dashboard";
/** Which pipeline a destination belongs to.
 *
 * Phase 2a of DESIGN_FLOW_PLAN.md. The 14 August audit's largest structural
 * finding was two pipelines interleaved in one interface, and that it is the
 * first thing a person hits: ten destinations in one row, in no order, with
 * nothing saying that Prompts and Social are world work and Designs and Score
 * are product work.
 *
 * This does not move anything. Relocating world screens is Phase 2b and waits
 * on the campaign UI shape (session handover §4.3). Grouping what is already
 * here depends on nothing anyone else is building, and answers the question a
 * newcomer actually has.
 */
type Pipeline = "product" | "world";

const PIPELINES: { id: Pipeline; label: string; blurb: string }[] = [
  {
    id: "product",
    label: "Product",
    blurb: "Evidence to a printed design.",
  },
  {
    id: "world",
    label: "World",
    blurb: "Canon to a photograph to a customer.",
  },
];

const VIEWS: { id: View; label: string; pipeline: Pipeline }[] = [
  // Product: evidence → research → concept → design → approved version → print.
  // Work leads because it is the answer to "what should I be doing", and the
  // other destinations are where its rows send you.
  { id: "work", label: "Work", pipeline: "product" },
  { id: "evidence", label: "Evidence", pipeline: "product" },
  { id: "research", label: "Research", pipeline: "product" },
  { id: "concepts", label: "Designs", pipeline: "product" },
  { id: "compose", label: "Compose", pipeline: "product" },
  { id: "design", label: "Score", pipeline: "product" },
  // World: canon → shot → photograph → decision → social → customer.
  { id: "dashboard", label: "Dashboard", pipeline: "world" },
  { id: "prompts", label: "Prompts", pipeline: "world" },
  { id: "print", label: "Print", pipeline: "world" },
  { id: "social", label: "Social", pipeline: "world" },
  { id: "email", label: "Email", pipeline: "world" },
];
const ADMIN_URL = "https://admin.shirtfaced.wtf";
const MOBILE = "@media screen and (max-width: 760px)";
const iconBase = {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  width: 24,
  height: 24,
  "aria-hidden": true,
};
const IconMenu = () => (
  <svg {...iconBase}>
    <path d="M3.5 7h17M3.5 12h17M3.5 17h17" />
  </svg>
);
const IconClose = () => (
  <svg {...iconBase}>
    <path d="M6 6l12 12M18 6L6 18" />
  </svg>
);
export function App({ themeName, onToggleTheme }: AppProps): React.JSX.Element {
  const [css, theme] = useStyletron();
  // Work is the front door: it is the one screen that answers what to do
  // without knowing which screen owns what.
  const [view, setView] = useState<View>("work");
  // What Work sent us to, so Designs can open straight onto it. Cleared once
  // consumed, so navigating away and back does not silently re-open it.
  const [focus, setFocus] = useState<{ conceptId: string; attemptId: string | null } | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const hairline = `1px solid color-mix(in srgb, ${theme.colors.contentPrimary} 10%, transparent)`;
  const item = (active: boolean) =>
    css({
      appearance: "none",
      border: "none",
      cursor: "pointer",
      fontFamily: "inherit",
      fontSize: "13px",
      fontWeight: 600,
      textTransform: "uppercase",
      borderRadius: "14px",
      padding: "8px 12px",
      backgroundColor: active ? theme.colors.contentPrimary : "transparent",
      color: active ? theme.colors.backgroundPrimary : theme.colors.contentPrimary,
      textDecoration: "none",
    });
  const pick = (id: View) => {
    setView(id);
    setMenuOpen(false);
  };
  // The group label. Quiet on purpose: it names the pipeline without competing
  // with the destinations, which are what a person is actually aiming at.
  const groupLabel = css({
    fontSize: "10px",
    fontWeight: 700,
    letterSpacing: "0.12em",
    textTransform: "uppercase",
    color: theme.colors.contentTertiary,
    alignSelf: "center",
    paddingRight: "2px",
    whiteSpace: "nowrap",
  });
  const divider = css({
    width: "1px",
    alignSelf: "stretch",
    marginTop: "8px",
    marginBottom: "8px",
    backgroundColor: `color-mix(in srgb, ${theme.colors.contentPrimary} 14%, transparent)`,
  });
  return (
    <div className={css({ minHeight: "100vh", backgroundColor: theme.colors.backgroundPrimary })}>
      <header
        className={css({
          position: "sticky",
          top: 0,
          zIndex: 40,
          borderBottom: hairline,
          backgroundColor: theme.colors.backgroundPrimary,
        })}
      >
        <div
          className={css({
            maxWidth: "1024px",
            margin: "auto",
            height: "64px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 16px",
          })}
        >
          <span className="wordmark">shirtfaced / studio</span>
          <nav
            className={css({
              display: "flex",
              gap: "4px",
              alignItems: "center",
              [MOBILE]: { display: "none" },
            })}
          >
            {PIPELINES.map((pipeline, index) => (
              <div
                key={pipeline.id}
                className={css({ display: "flex", gap: "4px", alignItems: "center" })}
              >
                {index > 0 ? <span className={divider} aria-hidden="true" /> : null}
                <span className={groupLabel} title={pipeline.blurb}>
                  {pipeline.label}
                </span>
                {VIEWS.filter((v) => v.pipeline === pipeline.id).map((v) => (
                  <button
                    key={v.id}
                    onClick={() => {
                      pick(v.id);
                    }}
                    className={item(view === v.id)}
                  >
                    {v.label}
                  </button>
                ))}
              </div>
            ))}
            <span className={divider} aria-hidden="true" />
            <a href={ADMIN_URL} className={item(false)}>
              Admin ↗
            </a>
            <button onClick={onToggleTheme} className={item(false)}>
              {themeName === "light" ? "Dark theme" : "Light theme"}
            </button>
          </nav>
          <button
            aria-label={menuOpen ? "Close menu" : "Open menu"}
            onClick={() => {
              setMenuOpen((x) => !x);
            }}
            className={css({
              display: "none",
              [MOBILE]: { display: "grid" },
              placeItems: "center",
              width: "44px",
              height: "44px",
              border: 0,
              background: "transparent",
            })}
          >
            {menuOpen ? <IconClose /> : <IconMenu />}
          </button>
        </div>
        {menuOpen ? (
          <nav
            className={css({
              display: "none",
              [MOBILE]: { display: "flex" },
              flexDirection: "column",
              gap: "4px",
              padding: "12px 16px 16px",
              borderTop: hairline,
            })}
          >
            {PIPELINES.map((pipeline) => (
              <div
                key={pipeline.id}
                className={css({ display: "flex", flexDirection: "column", gap: "4px" })}
              >
                <span
                  className={css({
                    fontSize: "10px",
                    fontWeight: 700,
                    letterSpacing: "0.12em",
                    textTransform: "uppercase",
                    color: theme.colors.contentTertiary,
                    paddingTop: "8px",
                  })}
                >
                  {pipeline.label} — {pipeline.blurb}
                </span>
                {VIEWS.filter((v) => v.pipeline === pipeline.id).map((v) => (
                  <button
                    key={v.id}
                    onClick={() => {
                      pick(v.id);
                    }}
                    className={item(view === v.id)}
                  >
                    {v.label}
                  </button>
                ))}
              </div>
            ))}
            <a href={ADMIN_URL} className={item(false)}>
              Admin ↗
            </a>
          </nav>
        ) : null}
      </header>
      <main
        className={css({
          maxWidth: "1024px",
          margin: "auto",
          padding: theme.sizing.scale900,
          paddingLeft: "16px",
          paddingRight: "16px",
        })}
      >
        {view === "work" ? (
          <WorkBench
            onOpen={(item: WorkItem) => {
              // Every row lands on the screen that can actually do the thing.
              setFocus({ conceptId: item.concept_id, attemptId: item.attempt_id });
              setView("concepts");
            }}
          />
        ) : view === "prompts" ? (
          <PromptWorkbench />
        ) : view === "print" ? (
          <PrintBench />
        ) : view === "compose" ? (
          <ComposeBench />
        ) : view === "concepts" ? (
          <DesignsBench
            focus={focus}
            onFocusConsumed={() => {
              setFocus(null);
            }}
          />
        ) : view === "design" ? (
          <DesignBench />
        ) : view === "evidence" ? (
          <VintageEvidenceBench />
        ) : view === "research" ? (
          <VintageResearchBench />
        ) : view === "social" ? (
          <SocialBench />
        ) : view === "email" ? (
          <EmailBench />
        ) : (
          <>
            <h1 className="display">Dashboard</h1>
            <ParagraphMedium>
              A private production tool for building coherent Shirtfaced photographic worlds.
            </ParagraphMedium>
            <WorldPage />
            <ServiceStatus />
          </>
        )}
      </main>
    </div>
  );
}

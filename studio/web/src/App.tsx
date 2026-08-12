/**
 * Application shell.
 *
 * The navigation and page frame every later screen sits inside. The shell is
 * admin's, deliberately: same translucent header, same icon toggle, same
 * mobile drawer with left-aligned rows and a separated footer action. Studio
 * and admin are one product, and the first thing a phone shows is the menu.
 */

import { useState } from "react";
import { useStyletron } from "baseui";
import { ParagraphMedium } from "baseui/typography";

import { ComposeBench } from "./components/ComposeBench";
import { DesignBench } from "./components/DesignBench";
import { DesignsBench } from "./components/DesignsBench";
import { EmailBench } from "./components/EmailBench";
import { PrintBench } from "./components/PrintBench";
import { PromptWorkbench } from "./components/PromptWorkbench";
import { ServiceStatus } from "./components/ServiceStatus";
import { SocialBench } from "./components/SocialBench";
import { WorldPage } from "./components/WorldPage";
import type { ThemeName } from "./theme";

export interface AppProps {
  themeName: ThemeName;
  onToggleTheme: () => void;
}

type View =
  "prompts" | "print" | "compose" | "concepts" | "design" | "social" | "email" | "dashboard";

const VIEWS: { id: View; label: string }[] = [
  { id: "prompts", label: "Prompts" },
  { id: "print", label: "Print" },
  { id: "compose", label: "Compose" },
  // The backlog. "Designs" holds concepts and their lineage; "Score" (below)
  // is the older single-image scorecard measurer, renamed so the two read as
  // different tools rather than a typo of each other.
  { id: "concepts", label: "Designs" },
  { id: "design", label: "Score" },
  { id: "social", label: "Social" },
  { id: "email", label: "Email" },
  { id: "dashboard", label: "Dashboard" },
];

const ADMIN_URL = "https://admin.shirtfaced.wtf";

/* Admin's icons, verbatim: same 2px-stroke, 24px-box convention. */
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

const MOBILE = "@media screen and (max-width: 760px)";

export function App({ themeName, onToggleTheme }: AppProps): React.JSX.Element {
  const [css, theme] = useStyletron();
  // Prompts first: generation happens elsewhere, so this is the screen that gets used.
  const [view, setView] = useState<View>("prompts");
  const [menuOpen, setMenuOpen] = useState(false);

  const hairline = `1px solid color-mix(in srgb, ${theme.colors.contentPrimary} 10%, transparent)`;

  const navItem = (active: boolean) =>
    css({
      appearance: "none",
      border: "none",
      cursor: "pointer",
      fontFamily: "inherit",
      fontSize: "13px",
      fontWeight: 600,
      letterSpacing: "0.02em",
      textTransform: "uppercase",
      borderRadius: "14px",
      paddingTop: "8px",
      paddingBottom: "8px",
      paddingLeft: "12px",
      paddingRight: "12px",
      backgroundColor: active ? theme.colors.contentPrimary : "transparent",
      color: active ? theme.colors.backgroundPrimary : theme.colors.contentPrimary,
      ":hover": { backgroundColor: active ? undefined : theme.colors.backgroundSecondary },
    });

  // The drawer rows, straight from admin's mobile panel: 48px tall, text left,
  // 15px, the active view a full-width ink pill.
  const drawerItem = (active: boolean) =>
    css({
      appearance: "none",
      border: "none",
      cursor: "pointer",
      fontFamily: "inherit",
      display: "flex",
      alignItems: "center",
      height: "48px",
      fontSize: "15px",
      fontWeight: 600,
      letterSpacing: "0.02em",
      textTransform: "uppercase",
      textDecoration: "none",
      textAlign: "left",
      borderRadius: "14px",
      paddingLeft: "12px",
      paddingRight: "12px",
      backgroundColor: active ? theme.colors.contentPrimary : "transparent",
      color: active ? theme.colors.backgroundPrimary : theme.colors.contentPrimary,
      ":hover": { backgroundColor: active ? undefined : theme.colors.backgroundSecondary },
    });

  const pick = (id: View) => {
    setView(id);
    setMenuOpen(false);
  };

  return (
    <div className={css({ minHeight: "100vh", backgroundColor: theme.colors.backgroundPrimary })}>
      <header
        className={css({
          position: "sticky",
          top: 0,
          zIndex: 40,
          // Admin's header: translucent paper over a blur, hairline ink rule.
          borderBottom: hairline,
          backgroundColor: `color-mix(in srgb, ${theme.colors.backgroundPrimary} 92%, transparent)`,
          backdropFilter: "blur(8px)",
        })}
      >
        <div
          className={css({
            maxWidth: "1024px",
            marginLeft: "auto",
            marginRight: "auto",
            height: "64px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "12px",
            paddingLeft: "16px",
            paddingRight: "16px",
          })}
        >
          <span className={`wordmark ${css({ fontSize: "22px" })}`}>
            shirtfaced{" "}
            <span className={css({ color: theme.colors.contentTertiary })}>/ studio</span>
          </span>

          {/* Desktop nav — above the breakpoint. */}
          <nav
            className={css({
              display: "flex",
              alignItems: "center",
              gap: "4px",
              flexWrap: "wrap",
              [MOBILE]: { display: "none" },
            })}
          >
            {VIEWS.map((item) => (
              <button
                key={item.id}
                type="button"
                aria-current={view === item.id ? "page" : undefined}
                onClick={() => {
                  pick(item.id);
                }}
                className={`press ${navItem(view === item.id)}`}
              >
                {item.label}
              </button>
            ))}
            {/* The other half of the tool. Admin's nav already links back here. */}
            <a
              href={ADMIN_URL}
              target="_blank"
              rel="noopener noreferrer"
              className={`press ${navItem(false)} ${css({ textDecoration: "none" })}`}
            >
              Admin ↗
            </a>
            <button
              type="button"
              onClick={onToggleTheme}
              className={`press ${css({
                appearance: "none",
                cursor: "pointer",
                fontFamily: "inherit",
                fontSize: "13px",
                fontWeight: 600,
                letterSpacing: "0.02em",
                textTransform: "uppercase",
                borderRadius: "14px",
                border: `1px solid ${theme.colors.borderOpaque}`,
                backgroundColor: "transparent",
                color: theme.colors.contentSecondary,
                paddingTop: "8px",
                paddingBottom: "8px",
                paddingLeft: "12px",
                paddingRight: "12px",
                marginLeft: "8px",
              })}`}
            >
              {themeName === "light" ? "Dark theme" : "Light theme"}
            </button>
          </nav>

          {/* Mobile toggle — admin's: a 44px icon button that swaps to a close. */}
          <button
            type="button"
            aria-label={menuOpen ? "Close menu" : "Open menu"}
            aria-expanded={menuOpen}
            aria-controls="studio-mobile-nav"
            onClick={() => {
              setMenuOpen((open) => !open);
            }}
            className={`press ${css({
              display: "none",
              [MOBILE]: { display: "grid" },
              placeItems: "center",
              height: "44px",
              width: "44px",
              marginRight: "-8px",
              appearance: "none",
              border: "none",
              cursor: "pointer",
              borderRadius: "14px",
              backgroundColor: "transparent",
              color: theme.colors.contentPrimary,
              ":hover": { backgroundColor: theme.colors.backgroundSecondary },
            })}`}
          >
            {menuOpen ? <IconClose /> : <IconMenu />}
          </button>
        </div>

        {/* Mobile drawer — admin's panel: hairline top, left-aligned rows,
            a separated full-width footer action. */}
        {menuOpen ? (
          <nav
            id="studio-mobile-nav"
            className={css({
              display: "none",
              [MOBILE]: { display: "block" },
              borderTop: hairline,
              paddingLeft: "16px",
              paddingRight: "16px",
              paddingBottom: "16px",
            })}
          >
            <ul
              className={css({
                listStyle: "none",
                margin: 0,
                padding: "12px 0 0",
                display: "flex",
                flexDirection: "column",
                gap: "4px",
              })}
            >
              {VIEWS.map((item) => (
                <li key={item.id}>
                  <button
                    type="button"
                    aria-current={view === item.id ? "page" : undefined}
                    onClick={() => {
                      pick(item.id);
                    }}
                    className={`press ${drawerItem(view === item.id)} ${css({ width: "100%" })}`}
                  >
                    {item.label}
                  </button>
                </li>
              ))}
              <li>
                <a
                  href={ADMIN_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={() => {
                    setMenuOpen(false);
                  }}
                  className={`press ${drawerItem(false)}`}
                >
                  Admin ↗
                </a>
              </li>
            </ul>
            <div className={css({ marginTop: "12px", borderTop: hairline, paddingTop: "12px" })}>
              <button
                type="button"
                onClick={onToggleTheme}
                className={`press ${css({
                  appearance: "none",
                  cursor: "pointer",
                  fontFamily: "inherit",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: "100%",
                  height: "48px",
                  fontSize: "13px",
                  fontWeight: 600,
                  letterSpacing: "0.02em",
                  textTransform: "uppercase",
                  borderRadius: "14px",
                  border: `1px solid ${theme.colors.borderOpaque}`,
                  backgroundColor: "transparent",
                  color: theme.colors.contentSecondary,
                })}`}
              >
                {themeName === "light" ? "Dark theme" : "Light theme"}
              </button>
            </div>
          </nav>
        ) : null}
      </header>

      <main
        className={css({
          maxWidth: "1024px",
          marginRight: "auto",
          marginLeft: "auto",
          paddingTop: theme.sizing.scale900,
          paddingRight: "16px",
          paddingBottom: theme.sizing.scale900,
          paddingLeft: "16px",
        })}
      >
        {view === "prompts" ? (
          <PromptWorkbench />
        ) : view === "print" ? (
          <PrintBench />
        ) : view === "compose" ? (
          <ComposeBench />
        ) : view === "concepts" ? (
          <DesignsBench />
        ) : view === "design" ? (
          <DesignBench />
        ) : view === "social" ? (
          <SocialBench />
        ) : view === "email" ? (
          <EmailBench />
        ) : (
          <>
            <h1 className={`display ${css({ fontSize: "40px", margin: "0 0 8px" })}`}>Dashboard</h1>
            <ParagraphMedium color={theme.colors.contentSecondary} marginTop={0}>
              A private production tool for building coherent Shirtfaced photographic worlds.
            </ParagraphMedium>

            <WorldPage />

            <div className={css({ marginTop: theme.sizing.scale900, maxWidth: "420px" })}>
              <ServiceStatus />
            </div>
          </>
        )}
      </main>
    </div>
  );
}

/** Application shell. */
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
  { id: "concepts", label: "Designs" },
  { id: "design", label: "Score" },
  { id: "social", label: "Social" },
  { id: "email", label: "Email" },
  { id: "dashboard", label: "Dashboard" },
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
  const [view, setView] = useState<View>("prompts");
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
          <nav className={css({ display: "flex", gap: "4px", [MOBILE]: { display: "none" } })}>
            {VIEWS.map((v) => (
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
            {VIEWS.map((v) => (
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

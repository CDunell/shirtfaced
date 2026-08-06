/**
 * Application shell.
 *
 * The navigation and page frame every later screen sits inside: the dashboard, the
 * world page, the generation review and the history list.
 */

import { useState } from "react";
import { useStyletron } from "baseui";
import { ParagraphMedium } from "baseui/typography";

import { PromptWorkbench } from "./components/PromptWorkbench";
import { ServiceStatus } from "./components/ServiceStatus";
import { WorldPage } from "./components/WorldPage";
import type { ThemeName } from "./theme";

export interface AppProps {
  themeName: ThemeName;
  onToggleTheme: () => void;
}

type View = "prompts" | "dashboard";

const VIEWS: { id: View; label: string }[] = [
  { id: "prompts", label: "Prompts" },
  { id: "dashboard", label: "Dashboard" },
];

export function App({ themeName, onToggleTheme }: AppProps): React.JSX.Element {
  const [css, theme] = useStyletron();
  // Prompts first: generation happens elsewhere, so this is the screen that gets used.
  const [view, setView] = useState<View>("prompts");

  // Admin's header, rebuilt: sticky, hairline rule, wordmark left, pill nav right.
  // Base Web's HeaderNavigation brings its own look, which is the look we are
  // moving away from, so the shell is plain markup and the components inside it
  // take the shared palette from theme.ts.
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

  return (
    <div className={css({ minHeight: "100vh", backgroundColor: theme.colors.backgroundPrimary })}>
      <header
        className={css({
          position: "sticky",
          top: 0,
          zIndex: 40,
          borderBottom: `1px solid ${theme.colors.borderOpaque}`,
          backgroundColor: theme.colors.backgroundPrimary,
        })}
      >
        <div
          className={css({
            maxWidth: "1024px",
            marginLeft: "auto",
            marginRight: "auto",
            minHeight: "64px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "12px",
            // A phone cannot fit both. Wrapping beats a sideways scroll.
            flexWrap: "wrap",
            paddingLeft: "16px",
            paddingRight: "16px",
            paddingTop: "8px",
            paddingBottom: "8px",
          })}
        >
          <span className={`wordmark ${css({ fontSize: "22px" })}`}>
            shirtfaced{" "}
            <span className={css({ color: theme.colors.contentTertiary })}>/ studio</span>
          </span>

          <nav className={css({ display: "flex", alignItems: "center", gap: "4px" })}>
            {VIEWS.map((item) => (
              <button
                key={item.id}
                type="button"
                aria-current={view === item.id ? "page" : undefined}
                onClick={() => {
                  setView(item.id);
                }}
                className={`press ${navItem(view === item.id)}`}
              >
                {item.label}
              </button>
            ))}
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
        </div>
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

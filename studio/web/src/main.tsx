/**
 * Entry point: Styletron engine, Base provider and theme state.
 */

import { StrictMode, useCallback, useState } from "react";
import { createRoot } from "react-dom/client";
import { BaseProvider } from "baseui";
import { Client as Styletron } from "styletron-engine-monolithic";
import { Provider as StyletronProvider } from "styletron-react";

import { App } from "./App";
import { initialThemeName, storeThemeName, THEMES, type ThemeName } from "./theme";

const engine = new Styletron();

function Root(): React.JSX.Element {
  const [themeName, setThemeName] = useState<ThemeName>(initialThemeName);

  const toggleTheme = useCallback(() => {
    setThemeName((current) => {
      const next: ThemeName = current === "light" ? "dark" : "light";
      storeThemeName(next);
      return next;
    });
  }, []);

  return (
    <StyletronProvider value={engine}>
      <BaseProvider theme={THEMES[themeName]}>
        <App themeName={themeName} onToggleTheme={toggleTheme} />
      </BaseProvider>
    </StyletronProvider>
  );
}

const container = document.getElementById("root");
if (!container) {
  throw new Error("The root element is missing from index.html.");
}

createRoot(container).render(
  <StrictMode>
    <Root />
  </StrictMode>,
);

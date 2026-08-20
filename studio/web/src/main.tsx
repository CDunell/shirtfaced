/**
 * Entry point.
 *
 * Used to also set up the Styletron engine and Base Web's BaseProvider here;
 * now that every component is Tailwind, App itself handles theme sync (see
 * useSyncDarkClass) and there's no provider tree left to build.
 */

import { StrictMode, useCallback, useState } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./App";
import "./index.css";
import { initialThemeName, storeThemeName, type ThemeName } from "./theme";

function Root(): React.JSX.Element {
  const [themeName, setThemeName] = useState<ThemeName>(initialThemeName);

  const toggleTheme = useCallback(() => {
    setThemeName((current) => {
      const next: ThemeName = current === "light" ? "dark" : "light";
      storeThemeName(next);
      return next;
    });
  }, []);

  return <App themeName={themeName} onToggleTheme={toggleTheme} />;
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

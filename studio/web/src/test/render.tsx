/**
 * Test render helper.
 *
 * Named `renderWithBase` from when every component needed Base Web's
 * StyletronProvider/BaseProvider context to render at all -- kept as-is since
 * 15+ test files import it by this name and there's nothing left for a rename
 * to fix functionally. `themeName` still threads through so the handful of
 * dark-mode-aware tests keep working the same way.
 */

import type { ReactElement } from "react";
import { render, type RenderResult } from "@testing-library/react";

import type { ThemeName } from "../theme";

export function renderWithBase(ui: ReactElement, themeName: ThemeName = "light"): RenderResult {
  document.documentElement.classList.toggle("dark", themeName === "dark");
  return render(ui);
}

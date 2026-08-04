/**
 * Test render helper.
 *
 * Base components read theme tokens through context, so every rendered component
 * needs the Styletron engine and BaseProvider around it.
 */

import type { ReactElement } from "react";
import { BaseProvider } from "baseui";
import { render, type RenderResult } from "@testing-library/react";
import { Client as Styletron } from "styletron-engine-monolithic";
import { Provider as StyletronProvider } from "styletron-react";

import { THEMES, type ThemeName } from "../theme";

export function renderWithBase(ui: ReactElement, themeName: ThemeName = "light"): RenderResult {
  const engine = new Styletron();

  return render(
    <StyletronProvider value={engine}>
      <BaseProvider theme={THEMES[themeName]}>{ui}</BaseProvider>
    </StyletronProvider>,
  );
}

import { screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SelectionPanel } from "./SelectionPanel";
import { renderWithBase } from "../test/render";
import { nextShot, stubApi } from "../test/stubs";

afterEach(() => {
  vi.unstubAllGlobals();
});

function render() {
  return renderWithBase(<SelectionPanel slug="world-01" />);
}

describe("SelectionPanel", () => {
  it("shows the selected shot with its product and camera", async () => {
    stubApi();

    render();

    await waitFor(() => {
      expect(screen.getByText(/W01-011 — Car interior transition/)).toBeInTheDocument();
    });
    expect(screen.getByText("Tote bag")).toBeInTheDocument();
    expect(screen.getByText("Rear seat")).toBeInTheDocument();
  });

  it("explains why that shot was chosen", async () => {
    stubApi();

    render();

    await waitFor(() => {
      expect(screen.getByText(/Lowest priority \(100\), then sequence \(11\)/)).toBeInTheDocument();
    });
  });

  it("lists the shots it set aside", async () => {
    stubApi();

    render();

    await waitFor(() => {
      expect(screen.getByText("1 shot set aside")).toBeInTheDocument();
    });
    expect(screen.getByText(/W01-001: already approved/)).toBeInTheDocument();
  });

  it("says plainly when no shot can be selected", async () => {
    stubApi({
      nextShot: nextShot({
        selected: null,
        reason: "No planned shot is eligible.",
        eligible_count: 0,
      }),
    });

    render();

    await waitFor(() => {
      expect(screen.getByText("No shot can be selected")).toBeInTheDocument();
    });
    expect(screen.queryByRole("button", { name: /Preview/ })).not.toBeInTheDocument();
  });

  it("reports a failed selection rather than showing nothing", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.reject(new TypeError("Failed to fetch"))),
    );

    render();

    await waitFor(() => {
      expect(screen.getByText(/could not be reached/)).toBeInTheDocument();
    });
  });
});

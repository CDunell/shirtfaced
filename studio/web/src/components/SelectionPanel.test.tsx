import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SelectionPanel } from "./SelectionPanel";
import { renderWithBase } from "../test/render";
import { nextShot, planPreview, stubApi } from "../test/stubs";

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

  it("does not build a prompt until asked", async () => {
    const spy = stubApi();

    render();
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Preview production prompt/ })).toBeInTheDocument();
    });

    expect(spy.mock.calls.some((call) => String(call[0]).endsWith("/plan-preview"))).toBe(false);
  });

  it("builds the production prompt on request", async () => {
    stubApi();

    render();
    await userEvent.click(await screen.findByRole("button", { name: /Preview production prompt/ }));

    await waitFor(() => {
      expect(
        screen.getByText(/Documentary 35mm photograph of friends reorganising a car/),
      ).toBeInTheDocument();
    });
  });

  it("says when nothing was billed", async () => {
    stubApi();

    render();
    await userEvent.click(await screen.findByRole("button", { name: /Preview production prompt/ }));

    await waitFor(() => {
      expect(
        screen.getByText(/No OpenAI request was made and nothing was billed/),
      ).toBeInTheDocument();
    });
  });

  it("does not claim a fake plan came from a model", async () => {
    stubApi({ planPreview: planPreview({ live: true }) });

    render();
    await userEvent.click(await screen.findByRole("button", { name: /Preview production prompt/ }));

    await waitFor(() => {
      expect(screen.getByText("Negative constraints")).toBeInTheDocument();
    });
    expect(screen.queryByText(/nothing was billed/)).not.toBeInTheDocument();
  });

  it("shows the negative constraints the prompt carries", async () => {
    stubApi();

    render();
    await userEvent.click(await screen.findByRole("button", { name: /Preview production prompt/ }));

    await waitFor(() => {
      expect(screen.getByText("No visible branding")).toBeInTheDocument();
    });
  });

  it("surfaces the reason a preview was refused", async () => {
    stubApi({
      planStatus: 404,
      planDetail: "Prompt preview is available in development mode only.",
    });

    render();
    await userEvent.click(await screen.findByRole("button", { name: /Preview production prompt/ }));

    await waitFor(() => {
      expect(screen.getByText(/development mode only/)).toBeInTheDocument();
    });
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

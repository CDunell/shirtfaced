import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { renderWithBase } from "./test/render";
import { stubApi } from "./test/stubs";

afterEach(() => {
  vi.unstubAllGlobals();
});

const noop = (): void => undefined;

/** The shell opens on Designs, so a dashboard assertion has to go there first. */
async function showDashboard(): Promise<void> {
  await userEvent.click(screen.getByRole("button", { name: "Dashboard" }));
}

describe("App", () => {
  it("renders the shell", async () => {
    stubApi();

    renderWithBase(<App themeName="light" onToggleTheme={noop} />);

    // The wordmark is admin's, with the product name swapped. It is lowercase and
    // split across two elements, so the whole banner is what gets read.
    expect(screen.getByRole("banner")).toHaveTextContent("shirtfaced / studio");
    // Designs is the default view. Studio is the product tool, so it opens on the
    // product queue; it used to open on Prompts, which is world work, and that is
    // the interleaving Phase 2a exists to stop.
    expect(screen.getByRole("heading", { name: "Designs" })).toBeInTheDocument();
    await showDashboard();
    expect(screen.getByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText("Live")).toBeInTheDocument();
    });
  });

  it("groups the destinations by pipeline rather than listing ten in a row", () => {
    // The 14 August audit's largest structural finding was two pipelines
    // interleaved in one interface, and that it is the first thing a person
    // hits. Nothing has moved -- but which is which is now stated.
    stubApi();

    renderWithBase(<App themeName="light" onToggleTheme={noop} />);

    const banner = screen.getByRole("banner");
    expect(banner).toHaveTextContent("Product");
    expect(banner).toHaveTextContent("World");
    // Product destinations lead, in the order the work happens.
    const labels = Array.from(banner.querySelectorAll("button")).map((b) => b.textContent);
    expect(labels.indexOf("Evidence")).toBeLessThan(labels.indexOf("Prompts"));
    expect(labels.indexOf("Designs")).toBeLessThan(labels.indexOf("Social"));
  });

  it("shows the world alongside the service status", async () => {
    stubApi();

    renderWithBase(<App themeName="light" onToggleTheme={noop} />);
    await showDashboard();

    await waitFor(() => {
      expect(screen.getByText("SHIRTFACED — WORLD 01")).toBeInTheDocument();
    });
    expect(screen.getByRole("heading", { name: "Shotlist" })).toBeInTheDocument();
  });

  it("shows the service version once the liveness check succeeds", async () => {
    stubApi({ health: { status: "ok", version: "9.9.9" } });

    renderWithBase(<App themeName="light" onToggleTheme={noop} />);
    await showDashboard();

    await waitFor(() => {
      expect(screen.getByText("version 9.9.9")).toBeInTheDocument();
    });
  });

  it("reports an unreachable service rather than pretending it is live", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.reject(new TypeError("Failed to fetch"))),
    );

    renderWithBase(<App themeName="light" onToggleTheme={noop} />);
    await showDashboard();

    await waitFor(() => {
      expect(screen.getByText("Unreachable")).toBeInTheDocument();
    });
    expect(screen.queryByText("Live")).not.toBeInTheDocument();
  });

  it("offers the opposite theme and reports the toggle", async () => {
    stubApi();
    const onToggleTheme = vi.fn();

    renderWithBase(<App themeName="light" onToggleTheme={onToggleTheme} />);
    await userEvent.click(screen.getByRole("button", { name: "Dark theme" }));

    expect(onToggleTheme).toHaveBeenCalledOnce();
  });

  it("re-checks the service on request", async () => {
    const spy = stubApi();

    renderWithBase(<App themeName="light" onToggleTheme={noop} />);
    await showDashboard();
    await waitFor(() => {
      expect(screen.getByText("Live")).toBeInTheDocument();
    });
    const healthCalls = (): number =>
      spy.mock.calls.filter((call) => String(call[0]).startsWith("/health")).length;
    const before = healthCalls();

    await userEvent.click(screen.getByRole("button", { name: "Check again" }));

    await waitFor(() => {
      expect(healthCalls()).toBeGreaterThan(before);
    });
  });
});

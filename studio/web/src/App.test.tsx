import userEvent from "@testing-library/user-event";
import { screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { renderWithBase } from "./test/render";
import { stubApi } from "./test/stubs";

afterEach(() => {
  vi.unstubAllGlobals();
});

const noop = (): void => undefined;

/**
 * The desktop sidebar (Phase 1 of docs/ADMIN_STUDIO_UI_OVERHAUL_PLAN.md) renders
 * every destination unconditionally -- no "Open menu" click needed to reach them,
 * unlike the hamburger-at-every-width header this replaced. The mobile drawer is
 * a separate, conditionally-rendered <aside> that only exists once opened; the
 * always-present one (found first, since it renders before any drawer could)
 * is the desktop sidebar these tests exercise.
 */
function sidebar(): HTMLElement {
  const aside = document.querySelector("aside");
  if (!aside) throw new Error("The sidebar is not on the page.");
  return aside;
}

/** The shell opens on Work, so a dashboard assertion has to go there first. */
async function showDashboard(): Promise<void> {
  await userEvent.click(within(sidebar()).getByRole("button", { name: "Dashboard" }));
}

describe("App", () => {
  it("renders the shell", async () => {
    stubApi();

    renderWithBase(<App themeName="light" onToggleTheme={noop} />);

    // The wordmark is admin's, with the product name swapped.
    expect(sidebar()).toHaveTextContent("shirtfaced / studio");
    // Work is the default view. It is the one screen that answers "what should I
    // be doing" without requiring you to know which screen owns what, which is
    // the plan's governing rule. It used to open on Prompts, which is world work.
    expect(screen.getByRole("heading", { name: "Work" })).toBeInTheDocument();
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

    const nav = sidebar();
    expect(nav).toHaveTextContent("Product");
    expect(nav).toHaveTextContent("World");
    // Product destinations lead, in the order the work happens.
    const labels = Array.from(nav.querySelectorAll("button")).map((b) => b.textContent);
    expect(labels.indexOf("Work")).toBeLessThan(labels.indexOf("Prompts"));
    expect(labels.indexOf("Designs")).toBeLessThan(labels.indexOf("Social"));
    // Work leads the product group: the other destinations are where its rows send you.
    expect(labels.indexOf("Work")).toBeLessThan(labels.indexOf("Evidence"));
  });

  it("no longer offers Compose or Score as destinations", () => {
    // Phase 5. They were three screens that each knew part of one journey.
    // The capabilities did not go anywhere -- they fold into Designs.
    stubApi();

    renderWithBase(<App themeName="light" onToggleTheme={noop} />);

    const labels = Array.from(sidebar().querySelectorAll("button")).map((b) => b.textContent);
    expect(labels).not.toContain("Compose");
    expect(labels).not.toContain("Score");
    expect(labels).toContain("Designs");
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
    await userEvent.click(within(sidebar()).getByRole("button", { name: "Dark theme" }));

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

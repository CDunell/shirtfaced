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

describe("App", () => {
  it("renders the shell", async () => {
    stubApi();

    renderWithBase(<App themeName="light" onToggleTheme={noop} />);

    expect(screen.getByText("Shirtfaced Studio")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText("Live")).toBeInTheDocument();
    });
  });

  it("shows the world alongside the service status", async () => {
    stubApi();

    renderWithBase(<App themeName="light" onToggleTheme={noop} />);

    await waitFor(() => {
      expect(screen.getByText("SHIRTFACED — WORLD 01")).toBeInTheDocument();
    });
    expect(screen.getByRole("heading", { name: "Shotlist" })).toBeInTheDocument();
  });

  it("shows the service version once the liveness check succeeds", async () => {
    stubApi({ health: { status: "ok", version: "9.9.9" } });

    renderWithBase(<App themeName="light" onToggleTheme={noop} />);

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

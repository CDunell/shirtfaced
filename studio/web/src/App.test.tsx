import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { renderWithBase } from "./test/render";

afterEach(() => {
  vi.unstubAllGlobals();
});

function stubHealth(response: () => Promise<Response>): void {
  vi.stubGlobal("fetch", vi.fn(response));
}

const noop = (): void => undefined;

describe("App", () => {
  it("renders the shell", async () => {
    stubHealth(() =>
      Promise.resolve(new Response(JSON.stringify({ status: "ok", version: "0.1.0" }))),
    );

    renderWithBase(<App themeName="light" onToggleTheme={noop} />);

    expect(screen.getByText("Shirtfaced Studio")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText("Live")).toBeInTheDocument();
    });
  });

  it("shows the service version once the liveness check succeeds", async () => {
    stubHealth(() =>
      Promise.resolve(new Response(JSON.stringify({ status: "ok", version: "9.9.9" }))),
    );

    renderWithBase(<App themeName="light" onToggleTheme={noop} />);

    await waitFor(() => {
      expect(screen.getByText("version 9.9.9")).toBeInTheDocument();
    });
  });

  it("reports an unreachable service rather than pretending it is live", async () => {
    stubHealth(() => Promise.reject(new TypeError("Failed to fetch")));

    renderWithBase(<App themeName="light" onToggleTheme={noop} />);

    await waitFor(() => {
      expect(screen.getByText("Unreachable")).toBeInTheDocument();
    });
    expect(screen.queryByText("Live")).not.toBeInTheDocument();
  });

  it("offers the opposite theme and reports the toggle", async () => {
    stubHealth(() =>
      Promise.resolve(new Response(JSON.stringify({ status: "ok", version: "0.1.0" }))),
    );
    const onToggleTheme = vi.fn();

    renderWithBase(<App themeName="light" onToggleTheme={onToggleTheme} />);
    await userEvent.click(screen.getByRole("button", { name: "Dark theme" }));

    expect(onToggleTheme).toHaveBeenCalledOnce();
  });

  it("re-checks the service on request", async () => {
    const spy = vi.fn(() =>
      Promise.resolve(new Response(JSON.stringify({ status: "ok", version: "0.1.0" }))),
    );
    vi.stubGlobal("fetch", spy);

    renderWithBase(<App themeName="light" onToggleTheme={noop} />);
    await waitFor(() => {
      expect(screen.getByText("Live")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole("button", { name: "Check again" }));

    await waitFor(() => {
      expect(spy.mock.calls.length).toBeGreaterThan(1);
    });
  });
});

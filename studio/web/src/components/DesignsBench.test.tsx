/**
 * The designs bench must show the backlog as it is and refuse unsigned work.
 *
 * The rules worth pinning: concepts render with their permanent numbers, a held
 * concept shows its salvage clause rather than reading as retired, and a
 * decision without a name never reaches the server.
 */

import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DesignsBench } from "./DesignsBench";
import { renderWithBase } from "../test/render";
import { conceptDetailView, conceptView, designAttemptView, stubApi } from "../test/stubs";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("DesignsBench", () => {
  it("lists the backlog with permanent numbers and statuses", async () => {
    stubApi({
      concepts: [
        conceptView(),
        conceptView({
          id: "concept-102",
          external_number: 102,
          slug: "102-the-drop-bear",
          title: "THE DROP BEAR",
          status: "retired",
          retirement: "unconditional",
        }),
      ],
      conceptNext: conceptView(),
    });

    renderWithBase(<DesignsBench />);

    await waitFor(() => {
      expect(screen.getByText("#102")).toBeInTheDocument();
    });
    expect(screen.getByText("THE DROP BEAR")).toBeInTheDocument();
    expect(screen.getByText("retired")).toBeInTheDocument();
    expect(screen.getByText("2 concepts")).toBeInTheDocument();
  });

  it("shows the queue's answer to what is next", async () => {
    stubApi({ concepts: [conceptView()], conceptNext: conceptView() });

    renderWithBase(<DesignsBench />);

    await waitFor(() => {
      expect(screen.getByText("Next up")).toBeInTheDocument();
    });
    expect(screen.getByRole("heading", { name: "#001 ABSOLUTE WEAPON" })).toBeInTheDocument();
  });

  it("shows a held concept's salvage clause when opened", async () => {
    const held = conceptView({
      id: "concept-88",
      external_number: 88,
      slug: "088-bin-night",
      title: "BIN NIGHT",
      status: "held",
      retirement: "conditional",
      salvage: "Retire as currently framed if it reads suburban-Australiana.",
    });
    stubApi({
      concepts: [held],
      conceptDetail: conceptDetailView({ ...held, attempts: [], versions: [] }),
    });

    renderWithBase(<DesignsBench />);

    await waitFor(() => {
      expect(screen.getByText("BIN NIGHT")).toBeInTheDocument();
    });
    await userEvent.click(screen.getByText("BIN NIGHT"));

    await waitFor(() => {
      expect(screen.getByText(/Held, not retired/)).toBeInTheDocument();
    });
  });

  it("refuses an unsigned decision without calling the server", async () => {
    const spy = stubApi({
      concepts: [],
      conceptQueue: [designAttemptView()],
    });

    renderWithBase(<DesignsBench />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
    });
    await userEvent.click(screen.getByRole("button", { name: "Approve" }));

    expect(screen.getByText("A decision needs a name against it.")).toBeInTheDocument();
    const decisionCalls = spy.mock.calls.filter(([url]) => String(url).includes("/decision"));
    expect(decisionCalls).toHaveLength(0);
  });

  it("sends a signed decision to the attempt's endpoint", async () => {
    const spy = stubApi({
      concepts: [],
      conceptQueue: [designAttemptView()],
      conceptAction: {
        id: "decision-1",
        decision: "approved",
        reason: null,
        note: null,
        instruction: null,
        actor: "owner",
        created_at: "2026-08-12T00:00:00Z",
      },
    });

    renderWithBase(<DesignsBench />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
    });
    await userEvent.type(screen.getByPlaceholderText("your name"), "owner");
    await userEvent.click(screen.getByRole("button", { name: "Approve" }));

    await waitFor(() => {
      const decisionCalls = spy.mock.calls.filter(([url]) =>
        String(url).includes("/api/concepts/attempts/attempt-1/decision"),
      );
      expect(decisionCalls).toHaveLength(1);
    });
  });
});

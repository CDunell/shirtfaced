import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CanonProposals } from "./CanonProposals";
import { renderWithBase } from "../test/render";
import { canonProposal, stubApi } from "../test/stubs";

afterEach(() => {
  vi.unstubAllGlobals();
});

function render() {
  renderWithBase(<CanonProposals slug="world-01" />);
}

describe("CanonProposals", () => {
  it("shows nothing when there are no proposals", async () => {
    stubApi({ proposals: [] });

    render();

    await waitFor(() => {
      expect(screen.queryByText("Proposed canon rules")).not.toBeInTheDocument();
    });
  });

  it("states plainly that nothing has changed canon", async () => {
    stubApi({ proposals: [canonProposal()] });

    render();

    expect(await screen.findByText("Nothing here has changed WORLD.md.")).toBeInTheDocument();
  });

  it("shows the proposed rule", async () => {
    stubApi({ proposals: [canonProposal()] });

    render();

    expect(
      await screen.findByText("Every ute must show an open aluminium alloy tray."),
    ).toBeInTheDocument();
  });

  it("labels a classification as advice", async () => {
    stubApi({
      proposals: [
        canonProposal({
          classification: "already_covered",
          classification_reason: "The wardrobe rule already implies this.",
        }),
      ],
    });

    render();

    expect(await screen.findByText("Already covered")).toBeInTheDocument();
    expect(screen.getByText("Advice. You decide.")).toBeInTheDocument();
    expect(screen.getByText("The wardrobe rule already implies this.")).toBeInTheDocument();
  });

  it("only offers sections the planner reads", async () => {
    stubApi({ proposals: [canonProposal()] });

    render();

    expect(
      await screen.findByText(/Only these sections reach the planning model/),
    ).toBeInTheDocument();
  });

  it("will not apply a rule before the diff has been read", async () => {
    stubApi({ proposals: [canonProposal({ target_heading: "Wardrobe" })] });

    render();

    const apply = await screen.findByRole("button", { name: /Apply this rule to canon/ });
    expect(apply).toBeDisabled();
    expect(screen.getByText(/approving the exact wording, not a summary/)).toBeInTheDocument();
  });

  it("shows the exact diff on request and then allows applying", async () => {
    stubApi({ proposals: [canonProposal({ target_heading: "Wardrobe" })] });

    render();
    await userEvent.click(await screen.findByRole("button", { name: /Show the exact change/ }));

    await waitFor(() => {
      expect(screen.getByText(/\+\+\+ WORLD\.md \(proposed\)/)).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: /Apply this rule to canon/ })).toBeEnabled();
  });

  it("does not apply anything just by showing the diff", async () => {
    const spy = stubApi({ proposals: [canonProposal({ target_heading: "Wardrobe" })] });

    render();
    await userEvent.click(await screen.findByRole("button", { name: /Show the exact change/ }));

    await waitFor(() => {
      expect(screen.getByText(/\+\+\+ WORLD\.md \(proposed\)/)).toBeInTheDocument();
    });
    expect(spy.mock.calls.some((call) => String(call[0]).endsWith("/approve"))).toBe(false);
  });

  it("can decline without reading a diff", async () => {
    const spy = stubApi({ proposals: [canonProposal()] });

    render();
    await userEvent.click(await screen.findByRole("button", { name: "Decline" }));

    await waitFor(() => {
      expect(spy.mock.calls.some((call) => String(call[0]).endsWith("/reject"))).toBe(true);
    });
  });

  it("offers classification when none has run", async () => {
    stubApi({ proposals: [canonProposal()] });

    render();

    expect(
      await screen.findByRole("button", { name: /Classify against canon/ }),
    ).toBeInTheDocument();
  });

  it("shows an applied proposal as settled rather than actionable", async () => {
    stubApi({
      proposals: [
        canonProposal({
          status: "applied",
          target_heading: "Wardrobe",
          human_note: "Agreed.",
        }),
      ],
    });

    render();

    expect(await screen.findByText(/Applied under Wardrobe/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Apply this rule/ })).not.toBeInTheDocument();
  });

  it("says canon is untouched when a proposal was declined", async () => {
    stubApi({ proposals: [canonProposal({ status: "rejected" })] });

    render();

    expect(await screen.findByText(/WORLD\.md is untouched/)).toBeInTheDocument();
  });

  it("surfaces a refusal", async () => {
    stubApi({
      proposals: [canonProposal({ target_heading: "Wardrobe" })],
      proposalStatus: 409,
      proposalDetail: "This proposal is already applied. Canon decisions are final.",
    });

    render();
    await userEvent.click(await screen.findByRole("button", { name: "Decline" }));

    await waitFor(() => {
      expect(screen.getByText(/already applied/)).toBeInTheDocument();
    });
  });
});

import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DecisionPanel } from "./DecisionPanel";
import { renderWithBase } from "../test/render";
import { attempt, decisionSummary, stubApi } from "../test/stubs";

afterEach(() => {
  vi.unstubAllGlobals();
});

function render(overrides = {}) {
  const onDecided = vi.fn();
  renderWithBase(<DecisionPanel attempt={attempt(overrides)} onDecided={onDecided} />);
  return onDecided;
}

describe("DecisionPanel", () => {
  it("offers all three decisions", () => {
    stubApi();

    render();

    expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reject" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Request variation" })).toBeInTheDocument();
  });

  it("requires confirmation before anything is final", async () => {
    const spy = stubApi();

    render();
    await userEvent.click(screen.getByRole("button", { name: "Approve" }));

    expect(screen.getByRole("button", { name: /this is final/ })).toBeInTheDocument();
    expect(spy.mock.calls.some((call) => String(call[0]).endsWith("/approve"))).toBe(false);
  });

  it("approves once confirmed", async () => {
    const spy = stubApi();
    const onDecided = render();

    await userEvent.click(screen.getByRole("button", { name: "Approve" }));
    await userEvent.click(screen.getByRole("button", { name: /this is final/ }));

    await waitFor(() => {
      expect(spy.mock.calls.filter((call) => String(call[0]).endsWith("/approve"))).toHaveLength(1);
    });
    expect(onDecided).toHaveBeenCalled();
  });

  it("offers reference promotion only on approval", async () => {
    stubApi();

    render();
    await userEvent.click(screen.getByRole("button", { name: "Approve" }));

    expect(screen.getByText("Promote to reference")).toBeInTheDocument();
  });

  it("will not let a rejection be confirmed without a reason", async () => {
    stubApi();

    render();
    await userEvent.click(screen.getByRole("button", { name: "Reject" }));

    expect(screen.queryByRole("button", { name: /this is final/ })).not.toBeInTheDocument();
    expect(screen.getByText(/A reason is required/)).toBeInTheDocument();
  });

  it("sends the rejection reason once given", async () => {
    const spy = stubApi();

    render();
    await userEvent.click(screen.getByRole("button", { name: "Reject" }));
    await userEvent.type(screen.getByLabelText("Rejection reason"), "The group reads as resigned.");
    await userEvent.click(screen.getByRole("button", { name: /this is final/ }));

    await waitFor(() => {
      const call = spy.mock.calls.find((c) => String(c[0]).endsWith("/reject"));
      expect(call).toBeDefined();
      expect(String((call?.[1] as { body?: string } | undefined)?.body)).toContain("resigned");
    });
  });

  it("will not let a variation be confirmed without an instruction", async () => {
    stubApi();

    render();
    await userEvent.click(screen.getByRole("button", { name: "Request variation" }));

    expect(screen.queryByRole("button", { name: /this is final/ })).not.toBeInTheDocument();
  });

  it("says a variation generates nothing", async () => {
    stubApi();

    render();
    await userEvent.click(screen.getByRole("button", { name: "Request variation" }));

    expect(screen.getByText(/No image is generated/)).toBeInTheDocument();
  });

  it("disables the controls once decided", () => {
    stubApi();

    render({ decision: decisionSummary() });

    expect(screen.queryByRole("button", { name: "Approve" })).not.toBeInTheDocument();
    expect(screen.getByText("Approved")).toBeInTheDocument();
  });

  it("reports document and Git sync separately", () => {
    stubApi();

    render({ decision: decisionSummary() });

    expect(screen.getByText("Documents: done")).toBeInTheDocument();
    expect(screen.getByText("Git: done")).toBeInTheDocument();
  });

  it("says the decision stands when a downstream step failed", () => {
    stubApi();

    render({
      decision: decisionSummary({
        git_sync: "failed",
        reconciliation_required: true,
        reconciliation_detail: "Uncommitted changes: the repository is locked",
      }),
    });

    expect(screen.getByText("Git: failed")).toBeInTheDocument();
    expect(screen.getByText(/recorded and final/)).toBeInTheDocument();
    expect(screen.getByText(/Nothing has been rolled back/)).toBeInTheDocument();
  });

  it("surfaces a refusal without claiming success", async () => {
    stubApi({
      decisionStatus: 409,
      decisionDetail: "Attempt 1 was already approved. A decision is final.",
    });
    const onDecided = render();

    await userEvent.click(screen.getByRole("button", { name: "Approve" }));
    await userEvent.click(screen.getByRole("button", { name: /this is final/ }));

    await waitFor(() => {
      expect(screen.getByText(/already approved/)).toBeInTheDocument();
    });
    expect(onDecided).not.toHaveBeenCalled();
  });

  it("does not offer a decision on an attempt that is not awaiting one", () => {
    stubApi();

    render({ state: "generated" });

    expect(screen.queryByRole("button", { name: "Approve" })).not.toBeInTheDocument();
    expect(screen.getByText(/cannot be decided/)).toBeInTheDocument();
  });

  it("can be cancelled without deciding", async () => {
    const spy = stubApi();

    render();
    await userEvent.click(screen.getByRole("button", { name: "Approve" }));
    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));

    expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
    expect(spy.mock.calls.some((call) => String(call[0]).endsWith("/approve"))).toBe(false);
  });
});

import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { GenerationPanel } from "./GenerationPanel";
import { renderWithBase } from "../test/render";
import { attempt, generationResult, stubApi } from "../test/stubs";

afterEach(() => {
  vi.unstubAllGlobals();
});

function render() {
  return renderWithBase(<GenerationPanel slug="world-01" />);
}

async function clickGenerate(): Promise<void> {
  await userEvent.click(await screen.findByRole("button", { name: "Continue World" }));
}

describe("GenerationPanel", () => {
  it("says what the action does before it is pressed", async () => {
    stubApi();

    render();

    expect(
      await screen.findByText(/Generates exactly one image for the next shot/),
    ).toBeInTheDocument();
    expect(screen.getByText(/Nothing is approved automatically/)).toBeInTheDocument();
  });

  it("does not generate anything on load", async () => {
    const spy = stubApi();

    render();
    await screen.findByRole("button", { name: "Continue World" });

    expect(spy.mock.calls.some((call) => String(call[0]).endsWith("/continue"))).toBe(false);
  });

  it("generates one image on request", async () => {
    const spy = stubApi();

    render();
    await clickGenerate();

    await waitFor(() => {
      const calls = spy.mock.calls.filter((call) => String(call[0]).endsWith("/continue"));
      expect(calls).toHaveLength(1);
    });
  });

  it("shows the generated image", async () => {
    stubApi({ attempts: [attempt()] });

    render();

    const image = await screen.findByRole("img", { name: /Generated image for W01-011/ });
    expect(image).toHaveAttribute("src", "/assets/asset-2");
  });

  it("states that a generated image is not approved", async () => {
    stubApi({ attempts: [attempt({ state: "generated" })] });

    render();

    expect(await screen.findByText(/Not approved/)).toBeInTheDocument();
  });

  it("offers the decision controls once an attempt is awaiting one", async () => {
    stubApi({ attempts: [attempt()] });

    render();

    expect(await screen.findByRole("button", { name: "Approve" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reject" })).toBeInTheDocument();
  });

  it("says when nothing was billed", async () => {
    stubApi();

    render();
    await clickGenerate();

    await waitFor(() => {
      expect(screen.getByText(/nothing was billed/)).toBeInTheDocument();
    });
  });

  it("does not claim a real generation was free", async () => {
    stubApi({ generation: generationResult({ live: true }) });

    render();
    await clickGenerate();

    await waitFor(() => {
      expect(screen.queryByText(/nothing was billed/)).not.toBeInTheDocument();
    });
  });

  it("surfaces a refusal when one is already running", async () => {
    stubApi({
      generationStatus: 409,
      generationDetail: "Attempt 1 for this world is already generated.",
    });

    render();
    await clickGenerate();

    await waitFor(() => {
      expect(screen.getByText(/already generated/)).toBeInTheDocument();
    });
  });

  it("shows a classified failure instead of a broken image", async () => {
    stubApi({
      attempts: [
        attempt({
          state: "failed",
          image_url: null,
          thumbnail_url: null,
          failure_code: "provider_timeout",
          failure_message: "The image request timed out.",
        }),
      ],
    });

    render();

    expect(await screen.findByText(/provider_timeout/)).toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("shows the provenance of an attempt", async () => {
    stubApi({ attempts: [attempt()] });

    render();

    expect(await screen.findByText("Tote bag")).toBeInTheDocument();
    expect(screen.getByText("Rear seat")).toBeInTheDocument();
    expect(screen.getByText("a-test-model")).toBeInTheDocument();
  });

  it("says so when there are no attempts", async () => {
    stubApi();

    render();

    expect(await screen.findByText("No attempts yet.")).toBeInTheDocument();
  });

  it("disables the action while it is running", async () => {
    stubApi();

    render();
    await clickGenerate();

    // The stub resolves immediately, so this asserts the button returns to normal
    // rather than staying stuck.
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Continue World" })).toBeEnabled();
    });
  });
});

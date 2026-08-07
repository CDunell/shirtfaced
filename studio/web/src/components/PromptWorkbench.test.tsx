/**
 * Choosing a scene shows what has already been written for it.
 *
 * The reason this is tested rather than clicked through: the browser tooling cannot
 * drive Base Web's Select in a way React accepts, so the one path that matters most
 * here — pick a scene, see its history — would otherwise go unverified.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { PromptWorkbench } from "./PromptWorkbench";
import { renderWithBase } from "../test/render";
import { shot, WORLD_SUMMARY, worldDetail } from "../test/stubs";
import * as client from "../api/client";

const SUNRISE = shot({ external_id: "W01-015", title: "Sunrise balcony", sequence: 15 });

function prompts(variation: number): client.Prompts {
  return {
    shot: SUNRISE,
    selection_reason: "W01-015 requested.",
    image_prompt: `image prompt ${String(variation)}`,
    video_prompt: `video prompt ${String(variation)}`,
    live: false,
    variation,
    written_at: "2026-08-06T01:00:00Z",
  };
}

beforeEach(() => {
  vi.restoreAllMocks();
  vi.spyOn(client, "fetchWorlds").mockResolvedValue([WORLD_SUMMARY]);
  vi.spyOn(client, "fetchWorld").mockResolvedValue(worldDetail({ shots: [SUNRISE] }));
});

async function chooseTheScene(): Promise<void> {
  const user = userEvent.setup();
  // The world is chosen for you when there is only one, so the scene select is the
  // second combobox on the page.
  const [, scene] = screen.getAllByRole("combobox");
  if (!scene) throw new Error("The scene select is not on the page.");
  await user.click(scene);
  await user.click(await screen.findByText(/W01-015/));
}

describe("PromptWorkbench", () => {
  it("shows what has already been written for the chosen scene", async () => {
    const history = vi
      .spyOn(client, "fetchPromptHistory")
      .mockResolvedValue({ shot: SUNRISE, variations: [prompts(2), prompts(1)] });

    renderWithBase(<PromptWorkbench />);
    await screen.findByText(/SHIRTFACED/);
    await chooseTheScene();

    await waitFor(() => {
      expect(history).toHaveBeenCalledWith("world-01", "W01-015", expect.anything());
    });
    // Newest first, and the first one written is the original rather than "variation 1".
    expect(await screen.findByText("variation 2")).toBeInTheDocument();
    expect(screen.getByText("original")).toBeInTheDocument();
    expect(screen.getByDisplayValue("image prompt 2")).toBeInTheDocument();
    expect(screen.getByDisplayValue("image prompt 1")).toBeInTheDocument();
  });

  it("says so when a scene has nothing written for it yet", async () => {
    vi.spyOn(client, "fetchPromptHistory").mockResolvedValue({ shot: SUNRISE, variations: [] });

    renderWithBase(<PromptWorkbench />);
    await screen.findByText(/SHIRTFACED/);
    await chooseTheScene();

    expect(
      await screen.findByText(/Nothing has been written for this scene yet/),
    ).toBeInTheDocument();
  });

  it("puts a newly written prompt above the ones it varies from", async () => {
    vi.spyOn(client, "fetchPromptHistory").mockResolvedValue({
      shot: SUNRISE,
      variations: [prompts(1)],
    });
    vi.spyOn(client, "writePrompts").mockResolvedValue(prompts(2));

    renderWithBase(<PromptWorkbench />);
    await screen.findByText(/SHIRTFACED/);
    await chooseTheScene();
    await screen.findByText("original");

    await userEvent.setup().click(screen.getByRole("button", { name: "Write prompts" }));

    // Both are present: writing again adds, it does not replace.
    expect(await screen.findByText("variation 2")).toBeInTheDocument();
    expect(screen.getByText("original")).toBeInTheDocument();
  });
});

import { screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { WorldPage } from "./WorldPage";
import { renderWithBase } from "../test/render";
import { shot, stubApi, worldDetail } from "../test/stubs";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("WorldPage", () => {
  it("shows the world name and status", async () => {
    stubApi();

    renderWithBase(<WorldPage />);

    await waitFor(() => {
      expect(screen.getByText("SHIRTFACED — WORLD 01")).toBeInTheDocument();
    });
    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("renders every shot in the shotlist", async () => {
    stubApi();

    renderWithBase(<WorldPage />);

    await waitFor(() => {
      expect(screen.getByText("Walking between venues")).toBeInTheDocument();
    });
    expect(screen.getByText("Bottle shop after close")).toBeInTheDocument();
    expect(screen.getByText("Car interior transition")).toBeInTheDocument();
  });

  it("shows each shot's status in words, not colour alone", async () => {
    stubApi();

    renderWithBase(<WorldPage />);

    const table = await screen.findByRole("table");
    await waitFor(() => {
      expect(within(table).getByText("Approved")).toBeInTheDocument();
    });
    expect(within(table).getByText("Rejected")).toBeInTheDocument();
    expect(within(table).getByText("Planned")).toBeInTheDocument();
  });

  it("reports the shot counts", async () => {
    stubApi();

    renderWithBase(<WorldPage />);

    await waitFor(() => {
      expect(screen.getByText("3 shots")).toBeInTheDocument();
    });
    expect(screen.getByText("Planned: 1")).toBeInTheDocument();
    expect(screen.getByText("Approved: 1")).toBeInTheDocument();
  });

  it("highlights the next planned shot with its hero product and camera", async () => {
    stubApi();

    renderWithBase(<WorldPage />);

    await waitFor(() => {
      expect(screen.getByText(/W01-011.*Car interior transition/)).toBeInTheDocument();
    });
    expect(screen.getByText(/Hero product: Tote bag/)).toBeInTheDocument();
    expect(screen.getByText(/Camera: Rear seat/)).toBeInTheDocument();
  });

  it("shows the loaded document hashes", async () => {
    stubApi();

    renderWithBase(<WorldPage />);

    await waitFor(() => {
      expect(screen.getByText("WORLD.md")).toBeInTheDocument();
    });
    expect(screen.getByText("CONTINUITY.md")).toBeInTheDocument();
    expect(screen.getByText("SHOTLIST.md")).toBeInTheDocument();
    expect(screen.getByText("aaaaaaaaaaaa…")).toBeInTheDocument();
  });

  it("says what to run when no world has been imported", async () => {
    stubApi({ worlds: [] });

    renderWithBase(<WorldPage />);

    await waitFor(() => {
      expect(screen.getByText(/import-world world-01/)).toBeInTheDocument();
    });
  });

  it("reports a failure rather than showing an empty page", async () => {
    stubApi({ worldStatus: 500 });

    renderWithBase(<WorldPage />);

    await waitFor(() => {
      expect(screen.getByText(/returned 500/)).toBeInTheDocument();
    });
  });

  it("handles a world whose planned shots are all done", async () => {
    stubApi({
      world: worldDetail({
        shots: [shot({ id: "s1", external_id: "W01-001", status: "approved" })],
        next_planned_shot: null,
      }),
    });

    renderWithBase(<WorldPage />);

    await waitFor(() => {
      expect(screen.getByText(/No planned shots remain/)).toBeInTheDocument();
    });
  });

  it("shows a dash where a shot has no hero product", async () => {
    stubApi({
      world: worldDetail({
        shots: [shot({ id: "s1", hero_product: null, camera_position: null })],
      }),
    });

    renderWithBase(<WorldPage />);

    const table = await screen.findByRole("table");
    await waitFor(() => {
      expect(within(table).getAllByText("—").length).toBeGreaterThanOrEqual(2);
    });
  });
});

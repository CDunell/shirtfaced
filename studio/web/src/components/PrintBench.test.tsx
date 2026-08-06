/**
 * The print bench.
 *
 * Dragging itself is not covered: the browser tooling cannot produce a pointer drag
 * without screenshots, and jsdom has no layout, so a test that pretended to drag
 * would be testing arithmetic rather than the interaction. What is covered is
 * everything either side of it — the library, the placement that comes back with a
 * photograph, and that settling on a placement saves it and renders.
 */

import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { PrintBench } from "./PrintBench";
import { renderWithBase } from "../test/render";
import * as client from "../api/client";

const PHOTO: client.Photo = {
  id: "photo-1",
  url: "/api/photos/photo-1/image",
  label: "W01-011 — Kerbside window chat",
  uploaded: false,
  width: 1536,
  height: 1024,
  placed: false,
};

const UPLOADED: client.Photo = { ...PHOTO, id: "photo-2", label: "kitchen.png", uploaded: true };

beforeEach(() => {
  vi.restoreAllMocks();
  // jsdom has no object URLs; the component makes one for every render it shows.
  vi.stubGlobal("URL", {
    ...URL,
    createObjectURL: vi.fn(() => "blob:printed"),
    revokeObjectURL: vi.fn(),
  });
  vi.spyOn(client, "fetchPhotos").mockResolvedValue([PHOTO]);
  vi.spyOn(client, "fetchDesigns").mockResolvedValue([{ name: "no-regrets.png" }]);
  vi.spyOn(client, "fetchPlacement").mockResolvedValue(null);
  vi.spyOn(client, "savePlacement").mockResolvedValue({
    corners: [
      [0, 0],
      [1, 0],
      [1, 1],
      [0, 1],
    ],
    settings: {},
    design: "no-regrets.png",
  });
  vi.spyOn(client, "printPhoto").mockResolvedValue(new Blob(["png"], { type: "image/png" }));
});

async function choosePhoto(label = "W01-011"): Promise<void> {
  const user = userEvent.setup();
  const [photos] = screen.getAllByRole("combobox");
  if (!photos) throw new Error("The photograph select is not on the page.");
  await user.click(photos);
  await user.click(await screen.findByText(new RegExp(label)));
}

describe("PrintBench", () => {
  it("says so when there is no artwork yet", async () => {
    vi.spyOn(client, "fetchDesigns").mockResolvedValue([]);

    renderWithBase(<PrintBench />);

    expect(await screen.findByText("No artwork yet")).toBeInTheDocument();
  });

  it("says so when nothing has been uploaded and nothing is approved", async () => {
    vi.spyOn(client, "fetchPhotos").mockResolvedValue([]);

    renderWithBase(<PrintBench />);

    expect(await screen.findByText(/Nothing here yet/)).toBeInTheDocument();
  });

  it("shows the photograph with a handle on each corner", async () => {
    const { container } = renderWithBase(<PrintBench />);
    await screen.findByText(/Drag the corners/);
    await choosePhoto();

    await waitFor(() => {
      expect(container.querySelector("polygon")).toBeInTheDocument();
    });
    // Handles are HTML rather than SVG: a circle in a viewBox stretched to the
    // photograph comes out an ellipse a few pixels across, which no finger can hit.
    expect(await screen.findAllByRole("slider")).toHaveLength(4);
  });

  it("marks where a photograph came from", async () => {
    vi.spyOn(client, "fetchPhotos").mockResolvedValue([UPLOADED]);

    renderWithBase(<PrintBench />);
    await screen.findByText(/Drag the corners/);
    await choosePhoto("kitchen.png");

    expect(await screen.findByText("uploaded")).toBeInTheDocument();
  });

  it("uses the placement a photograph already has", async () => {
    const saved: client.Corners = [
      [0.1, 0.2],
      [0.5, 0.2],
      [0.5, 0.6],
      [0.1, 0.6],
    ];
    vi.spyOn(client, "fetchPlacement").mockResolvedValue({
      corners: saved,
      settings: {},
      design: "no-regrets.png",
    });

    const { container } = renderWithBase(<PrintBench />);
    await screen.findByText(/Drag the corners/);
    await choosePhoto();

    await waitFor(() => {
      expect(container.querySelector("polygon")?.getAttribute("points")).toBe(
        "10,20 50,20 50,60 10,60",
      );
    });
  });

  it("saves the placement and renders when one is settled", async () => {
    renderWithBase(<PrintBench />);
    await screen.findByText(/Drag the corners/);
    await choosePhoto();

    await userEvent.setup().click(await screen.findByRole("button", { name: "Reset placement" }));

    await waitFor(() => {
      expect(client.savePlacement).toHaveBeenCalledWith("photo-1", {
        corners: expect.anything(),
        design: "no-regrets.png",
      });
    });
    expect(client.printPhoto).toHaveBeenCalledWith("photo-1", "no-regrets.png");
    // The render replaces the photograph, so what is on screen is the output.
    await waitFor(() => {
      expect(screen.getByAltText(PHOTO.label)).toHaveAttribute("src", "blob:printed");
    });
  });

  it("drags a corner to where the pointer went", async () => {
    /* The interaction the whole page exists for. jsdom has no layout, so the frame
       is given a known box and the maths is then real: a pointer at the middle of a
       200x100 frame is the corner at (0.5, 0.5). */
    const { container } = renderWithBase(<PrintBench />);
    await screen.findByText(/Drag the corners/);
    await choosePhoto();

    const handle = (await screen.findAllByRole("slider"))[0];
    if (!handle) throw new Error("No handles were rendered.");
    const frame = handle.parentElement;
    if (!frame) throw new Error("The handle is not inside the frame.");
    frame.getBoundingClientRect = () =>
      ({ left: 0, top: 0, width: 200, height: 100 }) as DOMRect;

    const at = (type: string, x: number, y: number) =>
      new PointerEvent(type, { bubbles: true, cancelable: true, pointerId: 1, clientX: x, clientY: y });

    handle.dispatchEvent(at("pointerdown", 76, 34));
    frame.dispatchEvent(at("pointermove", 100, 50));
    frame.dispatchEvent(at("pointerup", 100, 50));

    await waitFor(() => {
      // Only the corner that was grabbed moved, and it went where the pointer did.
      expect(container.querySelector("polygon")?.getAttribute("points")).toBe(
        "50,50 62,34 62,62 38,62",
      );
    });
    // Letting go is what saves and renders; dragging on its own does neither.
    expect(client.savePlacement).toHaveBeenCalled();
  });

  it("reports what the service said when a render fails", async () => {
    vi.spyOn(client, "printPhoto").mockRejectedValue(
      new client.ApiError(422, "Say where the design goes on this photograph first."),
    );

    renderWithBase(<PrintBench />);
    await screen.findByText(/Drag the corners/);
    await choosePhoto();
    await userEvent.setup().click(await screen.findByRole("button", { name: "Reset placement" }));

    expect(await screen.findByText(/Say where the design goes/)).toBeInTheDocument();
  });
});

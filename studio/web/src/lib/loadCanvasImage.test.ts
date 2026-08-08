import { afterEach, describe, expect, it, vi } from "vitest";
import { loadCanvasImage } from "./loadCanvasImage";

class FakeImage {
  private _src = "";
  naturalWidth = 1200;
  onload: (() => void) | null = null;
  onerror: (() => void) | null = null;

  get src(): string {
    return this._src;
  }

  set src(value: string) {
    this._src = value;
    queueMicrotask(() => {
      this.onload?.();
    });
  }
}

describe("loadCanvasImage", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("fetches stored WebP bytes before decoding for canvas use", async () => {
    const blob = new Blob(["webp-bytes"], { type: "image/webp" });
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        new Response(blob, { status: 200, headers: { "Content-Type": "image/webp" } }),
      );
    vi.stubGlobal("Image", FakeImage);
    const create = vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:studio-photo");
    const revoke = vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => undefined);

    const image = await loadCanvasImage("/api/photos/abc/image");

    expect(fetchMock).toHaveBeenCalledWith("/api/photos/abc/image", {
      credentials: "same-origin",
      cache: "no-store",
    });
    expect(image.src).toBe("blob:studio-photo");
    expect(create).toHaveBeenCalledWith(expect.objectContaining({ type: "image/webp" }));
    expect(revoke).toHaveBeenCalledWith("blob:studio-photo");
  });

  it("reports an HTTP failure before attempting image decode", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("missing", { status: 404 }));
    await expect(loadCanvasImage("/api/photos/missing/image")).rejects.toThrow("(404)");
  });
});

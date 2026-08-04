import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, fetchHealth } from "./client";

afterEach(() => {
  vi.unstubAllGlobals();
});

function stubFetch(implementation: typeof fetch): void {
  vi.stubGlobal("fetch", vi.fn(implementation));
}

describe("fetchHealth", () => {
  it("returns the parsed payload", async () => {
    stubFetch(() =>
      Promise.resolve(new Response(JSON.stringify({ status: "ok", version: "0.1.0" }))),
    );

    await expect(fetchHealth()).resolves.toEqual({ status: "ok", version: "0.1.0" });
  });

  it("requests the liveness endpoint on the same origin", async () => {
    const spy = vi.fn(() =>
      Promise.resolve(new Response(JSON.stringify({ status: "ok", version: "0.1.0" }))),
    );
    vi.stubGlobal("fetch", spy);

    await fetchHealth();

    expect(spy).toHaveBeenCalledWith(
      "/health",
      expect.objectContaining({ headers: expect.anything() }),
    );
  });

  it("raises ApiError carrying the status when the service responds with an error", async () => {
    stubFetch(() => Promise.resolve(new Response("nope", { status: 503 })));

    await expect(fetchHealth()).rejects.toMatchObject({ name: "ApiError", status: 503 });
  });

  it("raises ApiError with status 0 when the service cannot be reached", async () => {
    stubFetch(() => Promise.reject(new TypeError("Failed to fetch")));

    const error = await fetchHealth().catch((caught: unknown) => caught);

    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBe(0);
  });
});

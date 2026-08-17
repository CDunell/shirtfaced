import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CastBench } from "./CastBench";
import { renderWithBase } from "../test/render";

import type { CastAsset, CastMember, VisualAsset } from "../api/cast";

afterEach(() => {
  vi.unstubAllGlobals();
});

function asset(overrides: Partial<VisualAsset> = {}): VisualAsset {
  return {
    id: "11111111-1111-1111-1111-111111111111",
    kind: "cast",
    role: "head_shoulders_neutral",
    sha256: "a".repeat(64),
    mime_type: "image/png",
    width: 1402,
    height: 1122,
    byte_size: 1_900_000,
    aspect_ratio: 1.25,
    source_type: "generated",
    status: "approved",
    rights_status: "verified",
    description: null,
    approved_by: "owner",
    ...overrides,
  };
}

function reference(overrides: Partial<CastAsset> = {}): CastAsset {
  return {
    link_id: "22222222-2222-2222-2222-222222222222",
    role: "head_shoulders_neutral",
    sort_order: 0,
    is_primary: true,
    notes: null,
    asset: asset(),
    ...overrides,
  };
}

function damo(assets: CastAsset[]): CastMember {
  return {
    id: "33333333-3333-3333-3333-333333333333",
    slug: "damo",
    display_name: "Damo",
    description: null,
    status: "active",
    canonical_metadata: {},
    assets,
  };
}

interface StubResponse {
  ok: boolean;
  status: number;
  json: () => Promise<unknown>;
}

type FetchStub = (input: unknown, init?: unknown) => Promise<StubResponse>;

function respond(body: unknown, status = 200): Promise<StubResponse> {
  return Promise.resolve({ ok: status < 400, status, json: () => Promise.resolve(body) });
}

/** Both endpoints the bench opens with: the cast, and the offered roles. */
function stubCast(members: CastMember[], roles: string[] = ["shouting", "expression_bridge"]) {
  const fetchMock = vi.fn<FetchStub>((input) =>
    respond(String(input).includes("/api/cast/roles") ? roles : members),
  );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("CastBench", () => {
  it("shows a third reference without a fixed slot for it", async () => {
    stubCast([
      damo([
        reference(),
        reference({
          link_id: "44444444-4444-4444-4444-444444444444",
          role: "full_body_neutral",
          sort_order: 1,
          asset: asset({ id: "55555555-5555-5555-5555-555555555555", sha256: "b".repeat(64) }),
        }),
        reference({
          link_id: "66666666-6666-6666-6666-666666666666",
          role: "expression_bridge",
          sort_order: 2,
          is_primary: false,
          asset: asset({
            id: "77777777-7777-7777-7777-777777777777",
            sha256: "c".repeat(64),
            status: "pending",
          }),
        }),
      ]),
    ]);

    renderWithBase(<CastBench />);

    await waitFor(() => {
      expect(screen.getByText(/1 members · 3 references/i)).toBeInTheDocument();
    });
    expect(screen.getByText("expression bridge")).toBeInTheDocument();
    // The state a filesystem could not hold: arrived, not yet decided on.
    expect(screen.getByText("pending")).toBeInTheDocument();
  });

  it("offers approval for a pending reference and deprecation for an approved one", async () => {
    stubCast([
      damo([
        reference(),
        reference({
          link_id: "88888888-8888-8888-8888-888888888888",
          role: "shouting",
          sort_order: 1,
          is_primary: false,
          asset: asset({
            id: "99999999-9999-9999-9999-999999999999",
            sha256: "d".repeat(64),
            status: "pending",
          }),
        }),
      ]),
    ]);

    renderWithBase(<CastBench />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: "Deprecate" })).toBeInTheDocument();
  });

  it("says when an upload was bytes the library already held", async () => {
    const fetchMock = stubCast([damo([reference()])]);
    fetchMock.mockImplementation((input: unknown, init?: unknown): Promise<StubResponse> => {
      const url = String(input);
      const method = (init as { method?: string } | undefined)?.method ?? "GET";
      if (url.includes("/assets") && method === "POST") {
        return respond(
          reference({ role: "shouting", duplicate_of: "11111111-1111-1111-1111-111111111111" }),
          201,
        );
      }
      return respond(url.includes("/api/cast/roles") ? ["shouting"] : [damo([reference()])]);
    });

    renderWithBase(<CastBench />);
    await waitFor(() => {
      expect(screen.getByText(/1 members/i)).toBeInTheDocument();
    });

    const file = new File([new Uint8Array([1, 2, 3])], "damo.png", { type: "image/png" });
    const input = document.querySelector('input[type="file"]');
    if (!(input instanceof HTMLInputElement)) throw new Error("no file input rendered");
    await userEvent.upload(input, file);
    await userEvent.click(screen.getByText("Role"));
    await userEvent.click(await screen.findByText("shouting"));
    await userEvent.click(screen.getByRole("button", { name: "Add reference" }));

    await waitFor(() => {
      expect(screen.getByText(/already held/i)).toBeInTheDocument();
    });
  });
});

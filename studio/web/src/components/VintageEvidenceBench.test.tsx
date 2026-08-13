import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { VintageEvidenceBench } from "./VintageEvidenceBench";
import { renderWithBase } from "../test/render";

import type { EvidenceRecord } from "../api/client";

afterEach(() => {
  vi.unstubAllGlobals();
});

function record(overrides: Partial<EvidenceRecord> = {}): EvidenceRecord {
  return {
    listing_id: "406847192188",
    title: "Vintage 1993 Metallica No Where Else To Roam",
    brand: "Metallica",
    tradition: "band-merch",
    era_claim: "1990s",
    marketplace: "ebay",
    source_url: "https://example.test/item/1",
    images: ["/vintage-evidence/image/406847192188/image-01.jpg"],
    ...overrides,
  };
}

function stubEvidence(records: EvidenceRecord[]) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: () => Promise.resolve({ manifest: { image_count: 11544 }, records }),
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("VintageEvidenceBench", () => {
  it("reports what the cache holds rather than what was rendered", async () => {
    stubEvidence([record(), record({ listing_id: "900000000000001" })]);

    renderWithBase(<VintageEvidenceBench />);

    await waitFor(() => {
      expect(screen.getByText(/11544 images/)).toBeInTheDocument();
    });
  });

  it("shows a dash where the source never stated a brand", async () => {
    stubEvidence([record({ brand: "", listing_id: "900000000000002" })]);

    renderWithBase(<VintageEvidenceBench />);

    await waitFor(() => {
      expect(screen.getByText("—")).toBeInTheDocument();
    });
  });

  it("labels an archive record by its own marketplace, not eBay", async () => {
    stubEvidence([record({ listing_id: "900000000000003", marketplace: "archive" })]);

    renderWithBase(<VintageEvidenceBench />);

    await waitFor(() => {
      expect(screen.getByText(/Source/)).toBeInTheDocument();
    });
    expect(screen.queryByText(/eBay/)).not.toBeInTheDocument();
  });

  it("narrows the set as the search is typed", async () => {
    stubEvidence([
      record(),
      record({
        listing_id: "900000000000004",
        title: "Vintage 70s Hawaii Turtle Tee",
        brand: "",
      }),
    ]);

    renderWithBase(<VintageEvidenceBench />);
    await waitFor(() => {
      expect(screen.getByText("2 matching listings")).toBeInTheDocument();
    });

    await userEvent.type(screen.getByPlaceholderText("Search titles"), "hawaii");

    await waitFor(() => {
      expect(screen.getByText("1 matching listing")).toBeInTheDocument();
    });
  });

  it("says so when the cache cannot be reached", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));

    renderWithBase(<VintageEvidenceBench />);

    await waitFor(() => {
      expect(screen.getByText(/could not be reached|unavailable/i)).toBeInTheDocument();
    });
  });
});

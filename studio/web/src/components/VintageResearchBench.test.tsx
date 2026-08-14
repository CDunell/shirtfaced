import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { VintageResearchBench } from "./VintageResearchBench";
import { renderWithBase } from "../test/render";

import type { ResearchConcept, ResearchRun } from "../api/client";

afterEach(() => {
  vi.unstubAllGlobals();
});

function concept(overrides: Partial<ResearchConcept> = {}): ResearchConcept {
  return {
    concept_number: 1,
    title: "Two-headed mongrel",
    idea: "An animal hero rendered in crosshatch.",
    pass2_prompt: "Pure black artwork on a pure white background.",
    status: "pending",
    ...overrides,
  };
}

function run(overrides: Partial<ResearchRun> = {}): ResearchRun {
  return {
    id: "9b2ca526-0000-4000-8000-000000000000",
    concepts: [concept()],
    evidence_images: [],
    ...overrides,
  };
}

/** Routes by URL: a blanket stub would hide which endpoint produced a result. */
function stubRoutes(runs: ResearchRun[], onPost?: (url: string, body: unknown) => void) {
  const fetchMock = vi.fn((url: string, init?: RequestInit) => {
    if (init?.method === "POST" && !url.includes("/manual/")) {
      // init.body is always the JSON string the client sends; narrowed so the
      // parse is not reading a Blob or a stream's default stringification.
      const raw = typeof init.body === "string" ? init.body : null;
      onPost?.(url, raw === null ? undefined : JSON.parse(raw));
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve(
            url.includes("/pipeline")
              ? {
                  design_concept_id: "c1",
                  attempt_id: "a1",
                  attempt_number: 3,
                  state: "pending",
                }
              : concept({ status: "approved" }),
          ),
      });
    }
    if (url.includes("/manual/prepare")) {
      onPost?.(url, undefined);
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            pass1_prompt: "You are a print on demand design research expert.",
            pass2_prompt: "Make these 10 t-shirt design prompts more detailed.",
            evidence_filters: {},
            evidence_listing_ids: ["406847192188"],
            evidence_images: [
              {
                listing_id: "406847192188",
                filename: "image-01.jpg",
                image_url: "/vintage-evidence/image/406847192188/image-01.jpg",
              },
            ],
          }),
      });
    }
    if (url.includes("/api/vintage-evidence")) {
      // The bench builds its era and tradition options from the evidence, so a
      // stub that does not answer this leaves it with nothing to pick from.
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            manifest: { image_count: 4 },
            records: [
              {
                listing_id: "406847192188",
                title: "Vintage 1993 tour tee",
                brand: "",
                tradition: "band-merch",
                era_claim: "1990s",
                images: ["/vintage-evidence/image/406847192188/image-01.jpg"],
              },
            ],
          }),
      });
    }
    if (url.includes("design-concepts")) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve([{ id: "c1", number: 7, title: "Ibis" }]),
      });
    }
    if (/\/runs\/[^/]+$/.test(url)) {
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(runs[0]) });
    }
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(runs) });
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("VintageResearchBench", () => {
  it("opens on the most recent run", async () => {
    stubRoutes([run()]);

    renderWithBase(<VintageResearchBench />);

    await waitFor(() => {
      expect(screen.getByText(/Two-headed mongrel/)).toBeInTheDocument();
    });
  });

  it("offers a decision on every concept", async () => {
    stubRoutes([run()]);

    renderWithBase(<VintageResearchBench />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: "Reject" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save edit" })).toBeInTheDocument();
  });

  it("sends the decision to the concept endpoint", async () => {
    const posted: { url: string; body: unknown }[] = [];
    stubRoutes([run()], (url, body) => posted.push({ url, body }));

    renderWithBase(<VintageResearchBench />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
    });
    await userEvent.click(screen.getByRole("button", { name: "Approve" }));

    await waitFor(() => {
      expect(posted).toHaveLength(1);
    });
    expect(posted[0]?.url).toContain("/concepts/1");
    expect(posted[0]?.body).toMatchObject({ status: "approved" });
  });

  it("warns that a run is slow rather than looking hung", async () => {
    stubRoutes([run()]);

    renderWithBase(<VintageResearchBench />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Run both passes/ })).toBeInTheDocument();
    });
  });

  it("only offers the pipeline once a concept is approved", async () => {
    stubRoutes([run({ concepts: [concept({ status: "approved" })] })]);

    renderWithBase(<VintageResearchBench />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Send to design pipeline" })).toBeInTheDocument();
    });
  });

  it("sends to the endpoint that creates the attempt, and says which", async () => {
    const posted: { url: string; body: unknown }[] = [];
    stubRoutes([run({ concepts: [concept({ status: "approved" })] })], (url, body) =>
      posted.push({ url, body }),
    );

    renderWithBase(<VintageResearchBench />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Send to design pipeline" })).toBeInTheDocument();
    });
    await userEvent.click(screen.getByText("Design concept"));
    await userEvent.click(await screen.findByText(/#7 Ibis/));
    await userEvent.click(screen.getByRole("button", { name: "Send to design pipeline" }));

    await waitFor(() => {
      expect(screen.getByText(/Attempt 3 created/)).toBeInTheDocument();
    });
    // vintage_design creates the DesignAttempt; vintage_research only records it.
    expect(posted.at(-1)?.url).toContain("/api/vintage-design/runs/");
  });

  it("offers a manual path that costs nothing, alongside the billed one", async () => {
    stubRoutes([run()]);

    renderWithBase(<VintageResearchBench />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Prepare manual run/ })).toBeInTheDocument();
    });
    // The API path stays available, and says plainly that it bills.
    expect(screen.getByRole("button", { name: /billed/ })).toBeInTheDocument();
  });

  it("hands over the prompt and the selected images without calling a model", async () => {
    const posted: { url: string; body: unknown }[] = [];
    stubRoutes([run()], (url, body) => posted.push({ url, body }));

    renderWithBase(<VintageResearchBench />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Prepare manual run/ })).toBeInTheDocument();
    });
    await userEvent.click(screen.getByRole("button", { name: /Prepare manual run/ }));

    await waitFor(() => {
      expect(screen.getByPlaceholderText('{"concepts": [...]}')).toBeInTheDocument();
    });
    expect(posted.at(-1)?.url).toContain("/manual/prepare");
    // Nothing went to the endpoint that spends money.
    expect(posted.every((p) => !p.url.endsWith("/runs"))).toBe(true);
  });

  it("offers eras as options with counts, not a free-text box", async () => {
    stubRoutes([run()]);

    renderWithBase(<VintageResearchBench />);

    // filter_evidence matches era_claim by exact equality, so a typed "90s"
    // returns nothing and explains nothing. The picker cannot be wrong.
    await waitFor(() => {
      expect(screen.getByText("All eras")).toBeInTheDocument();
    });
    expect(screen.getByText("All traditions")).toBeInTheDocument();
    expect(screen.queryByPlaceholderText("Era, e.g. 1990s")).not.toBeInTheDocument();
  });

  it("labels the image count instead of showing a bare number", async () => {
    stubRoutes([run()]);

    renderWithBase(<VintageResearchBench />);

    await waitFor(() => {
      expect(screen.getByText("Images per run")).toBeInTheDocument();
    });
  });

  it("survives records that carry no era or tradition at all", async () => {
    // 233 of 3,639 live records have neither field -- newer eBay agent output
    // with a different shape. Calling .trim() on those threw and unmounted the
    // whole bench, which is what a blank page was.
    const fetchMock = vi.fn((url: string) => {
      if (url.includes("/api/vintage-evidence")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () =>
            Promise.resolve({
              manifest: {},
              records: [
                { listing_id: "406847192188", images: ["/a.jpg"] },
                {
                  listing_id: "900000000000001",
                  era_claim: "1990s",
                  tradition: "skate",
                  images: ["/b.jpg"],
                },
              ],
            }),
        });
      }
      if (url.includes("design-concepts")) {
        return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve([]) });
      }
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve([run()]) });
    });
    vi.stubGlobal("fetch", fetchMock);

    renderWithBase(<VintageResearchBench />);

    await waitFor(() => {
      expect(screen.getByText("All eras")).toBeInTheDocument();
    });
    // Rendered rather than blank, and the one usable value is still offered.
    expect(screen.getByText(/Vintage Research/i)).toBeInTheDocument();
  });

  it("hides the pipeline while a concept is still pending", async () => {
    stubRoutes([run()]);

    renderWithBase(<VintageResearchBench />);
    await waitFor(() => {
      expect(screen.getByText(/Two-headed mongrel/)).toBeInTheDocument();
    });

    expect(
      screen.queryByRole("button", { name: "Send to design pipeline" }),
    ).not.toBeInTheDocument();
  });
});

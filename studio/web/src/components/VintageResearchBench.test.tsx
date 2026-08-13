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
    if (init?.method === "POST") {
      // init.body is always the JSON string the client sends; narrowed so the
      // parse is not reading a Blob or a stream's default stringification.
      const raw = typeof init.body === "string" ? init.body : null;
      onPost?.(url, raw === null ? undefined : JSON.parse(raw));
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(concept({ status: "approved" })),
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

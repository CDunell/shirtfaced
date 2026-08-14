/**
 * The brief is the constitution's steps 1-4 and 6, and the exit test is that an
 * attempt cannot open without two of them while the advisor is visible as they
 * are chosen. These test that, and the wording that makes it followable.
 */

import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { BriefPanel } from "./BriefPanel";
import { renderWithBase } from "../test/render";
import { briefView, stubApi } from "../test/stubs";

afterEach(() => {
  vi.unstubAllGlobals();
});

const noop = (): void => undefined;

function panel() {
  return <BriefPanel conceptId="concept-1" conceptText="SECOND BREAKFAST" onChanged={noop} />;
}

describe("BriefPanel", () => {
  it("says what is missing before any artwork, not after", async () => {
    stubApi({});

    renderWithBase(panel());

    expect(await screen.findByText("Before any artwork")).toBeInTheDocument();
    expect(screen.getByText(/an attempt cannot open without them/)).toBeInTheDocument();
  });

  it("offers the constitution's five collection roles, not domain.ts's six", async () => {
    stubApi({});

    renderWithBase(panel());

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Collection role: Anchor" })).toBeInTheDocument();
    });
    for (const role of ["Anchor", "Core", "Expression", "Hero", "Collaboration"]) {
      expect(screen.getByRole("button", { name: `Collection role: ${role}` })).toBeInTheDocument();
    }
    // domain.ts carried these and the constitution does not.
    expect(screen.queryByRole("button", { name: /Staple/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Capsule/ })).not.toBeInTheDocument();
  });

  it("offers all nine graphic archetypes and all eight layouts", async () => {
    stubApi({});

    renderWithBase(panel());

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Graphic archetype: Typographic hero" }),
      ).toBeInTheDocument();
    });
    expect(screen.getAllByRole("button", { name: /^Graphic archetype: / })).toHaveLength(9);
    expect(screen.getAllByRole("button", { name: /^Layout archetype: / })).toHaveLength(8);
  });

  it("shows the advisor's recommendation with its evidence and confidence", async () => {
    // design_advisor answers from 12,151 measured images and nothing called it
    // before Phase 4.
    stubApi({});

    renderWithBase(panel());

    expect(await screen.findByTestId("advisor")).toBeInTheDocument();
    expect(screen.getByText(/S2 emblem/)).toBeInTheDocument();
    expect(screen.getByText(/412 measured images/)).toBeInTheDocument();
    expect(screen.getByText(/It will not say: subject matter/)).toBeInTheDocument();
  });

  it("records a choice rather than preventing one against the advice", async () => {
    const spy = stubApi({});

    renderWithBase(panel());

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Collection role: Hero" })).toBeInTheDocument();
    });
    await userEvent.click(screen.getByRole("button", { name: "Collection role: Hero" }));

    await waitFor(() => {
      const saved = spy.mock.calls.filter(
        ([url, init]) =>
          String(url).endsWith("/brief") && (init as RequestInit | undefined)?.method === "PUT",
      );
      expect(saved.length).toBeGreaterThan(0);
    });
  });

  it("says the product is defined once both gating choices are made", async () => {
    stubApi({
      brief: briefView({
        collection_role: "core",
        graphic_archetype: "typographic_hero",
        ready_for_artwork: true,
        next_action: "The product is defined. Start an attempt, and the brief goes with it.",
      }),
    });

    renderWithBase(panel());

    expect(await screen.findByText("The product is defined")).toBeInTheDocument();
    expect(screen.getByText(/Start an attempt/)).toBeInTheDocument();
  });
});

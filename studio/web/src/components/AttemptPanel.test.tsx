/**
 * The attempt panel is the whole flow, so these pin the rules that make it a
 * flow rather than a form.
 *
 * The exit test is a person who has not used the tool getting from a research
 * concept to an approved version without being told which screen to visit. The
 * things that decide whether that works are: the next action is stated, the
 * artwork has somewhere to land, the scorecard is answerable, and approval is
 * refused until it is earned. Each is tested here.
 */

import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AttemptPanel } from "./AttemptPanel";
import { renderWithBase } from "../test/render";
import { conceptDetailView, designAttemptView, reviewView, stubApi } from "../test/stubs";

afterEach(() => {
  vi.unstubAllGlobals();
});

function panel(attempt = designAttemptView({ state: "generated" })) {
  return (
    <AttemptPanel
      concept={conceptDetailView({ attempts: [attempt] })}
      attempt={attempt}
      actor="owner"
      onChanged={() => undefined}
    />
  );
}

describe("AttemptPanel", () => {
  it("states what to do next before anything else", async () => {
    stubApi({});

    renderWithBase(panel());

    expect(await screen.findByText("Do this next")).toBeInTheDocument();
    // The sentence itself, once the review has loaded -- not the heading above
    // it, which renders before anything is known.
    expect(await screen.findByText(/Measure it/)).toBeInTheDocument();
  });

  it("offers the brief to take away and no generate button", async () => {
    // Phase 0.1: the app owns the brief, the record, the measurement, the
    // judgement and the decision -- not the pixels. A generate button here
    // would be a promise the app has decided not to keep.
    stubApi({});

    renderWithBase(panel());

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Copy brief" })).toBeInTheDocument();
    });
    expect(screen.queryByRole("button", { name: /Generate/i })).not.toBeInTheDocument();
  });

  it("gives the artwork somewhere to land", async () => {
    // uploadAsset existed with zero call sites, which meant every attempt was
    // stuck in `planned` and could never be submitted, decided or approved.
    stubApi({});

    renderWithBase(panel(designAttemptView({ state: "planned", assets: [] })));

    await waitFor(() => {
      expect(screen.getByLabelText("Attach artwork to this attempt")).toBeInTheDocument();
    });
    expect(screen.getByText(/Drop the artwork here/)).toBeInTheDocument();
  });

  it("renders the scorecard in the constitution's three groups", async () => {
    stubApi({});

    renderWithBase(panel());

    await waitFor(() => {
      expect(screen.getByText("Validate recognition")).toBeInTheDocument();
    });
    expect(screen.getByText("Validate production")).toBeInTheDocument();
    expect(screen.getByText("Review against the collection")).toBeInTheDocument();
    // The question, not the field name.
    expect(
      screen.getByText("Within three seconds, is the main visual idea identifiable?"),
    ).toBeInTheDocument();
  });

  it("shows why a design cannot be approved rather than only that it cannot", async () => {
    stubApi({});

    renderWithBase(panel());

    await waitFor(() => {
      expect(screen.getByText("3 gates not answered")).toBeInTheDocument();
    });
    expect(screen.getByText("2 categories not rated")).toBeInTheDocument();
    expect(screen.getByText("0/100")).toBeInTheDocument();
  });

  it("refuses approval until the scorecard supports it, and says so", async () => {
    stubApi({ attemptReview: reviewView() });

    renderWithBase(panel(designAttemptView({ state: "awaiting_decision" })));

    expect(await screen.findByText(/Approve is unavailable/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Approve" })).toBeDisabled();
    // Refusing needs no rubric, so these stay available.
    expect(screen.getByRole("button", { name: "Reject" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Ask for a variation" })).toBeEnabled();
  });

  it("allows approval once the scorecard supports it", async () => {
    stubApi({
      attemptReview: reviewView({
        evaluation: {
          ...(reviewView().evaluation as Record<string, unknown>),
          eligibleForDesignApproval: true,
          percentage: 84,
          band: "revise_selectively",
          bandLabel: "Strong, revise selectively",
          untestedHardGates: [],
          unratedCategories: [],
          blockers: [],
        },
      }),
    });

    renderWithBase(panel(designAttemptView({ state: "awaiting_decision" })));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Approve" })).toBeEnabled();
    });
    expect(screen.getByText("84/100")).toBeInTheDocument();
    expect(screen.getByText(/Every gate answered, every floor met/)).toBeInTheDocument();
  });

  it("asks for the three things Print needs before a version exists", async () => {
    // A raster brought back from a paid interface carries no millimetres, so
    // the print width is a decision recorded at approval, not a property read
    // off the file.
    stubApi({});

    renderWithBase(panel(designAttemptView({ state: "approved" })));

    await waitFor(() => {
      expect(screen.getByText("Record the approved version")).toBeInTheDocument();
    });
    expect(screen.getByText("Garment")).toBeInTheDocument();
    expect(screen.getByText("Print zone")).toBeInTheDocument();
    expect(screen.getByText("Print width (mm)")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Record approved design/ })).toBeDisabled();
  });

  it("posts the answered gate to the review endpoint", async () => {
    const spy = stubApi({});

    renderWithBase(panel());

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Dominant proposition is clear: Pass" }),
      ).toBeInTheDocument();
    });
    await userEvent.click(
      screen.getByRole("button", { name: "Dominant proposition is clear: Pass" }),
    );

    await waitFor(() => {
      const saved = spy.mock.calls.filter(([url]) =>
        String(url).includes("/api/concepts/attempts/attempt-1/review"),
      );
      expect(saved.length).toBeGreaterThan(1);
    });
  });

  it("says a measurement is a starting point rather than a verdict", async () => {
    stubApi({});

    renderWithBase(
      panel(
        designAttemptView({
          state: "generated",
          assets: [
            {
              id: "asset-1",
              kind: "artwork",
              relative_path: "a.png",
              sha256: "0".repeat(64),
              mime_type: "image/png",
              width: 100,
              height: 100,
              byte_size: 10,
            },
          ],
        }),
      ),
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Measure this artwork" })).toBeInTheDocument();
    });
    expect(screen.getByText(/never overwrites/)).toBeInTheDocument();
    expect(screen.getByText(/not a verdict/)).toBeInTheDocument();
  });
});

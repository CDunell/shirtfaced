import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ReviewPanel } from "./ReviewPanel";
import { renderWithBase } from "../test/render";
import { gate, review } from "../test/stubs";

describe("ReviewPanel", () => {
  it("shows the recommendation and states that it is only advice", () => {
    renderWithBase(<ReviewPanel review={review()} />);

    expect(screen.getByText("Approval recommended")).toBeInTheDocument();
    expect(screen.getByText("This is advice. You decide.")).toBeInTheDocument();
  });

  it("does not present a recommendation as a decision", () => {
    renderWithBase(<ReviewPanel review={review({ recommendation: "REJECT_RECOMMENDED" })} />);

    expect(screen.getByText("Rejection recommended")).toBeInTheDocument();
    expect(screen.queryByText("Rejected")).not.toBeInTheDocument();
  });

  it("shows all five scores and both compliance flags", () => {
    renderWithBase(<ReviewPanel review={review()} />);

    expect(screen.getByText("Mood 4/5")).toBeInTheDocument();
    expect(screen.getByText("Story 4/5")).toBeInTheDocument();
    expect(screen.getByText("Branding compliant")).toBeInTheDocument();
    expect(screen.getByText("Vehicle compliant")).toBeInTheDocument();
  });

  it("marks a branding breach clearly", () => {
    renderWithBase(<ReviewPanel review={review({ branding_compliant: false })} />);

    expect(screen.getByText("Branding breach")).toBeInTheDocument();
  });

  it("renders every gate with its evidence", () => {
    renderWithBase(<ReviewPanel review={review()} />);

    expect(screen.getByText("Mood")).toBeInTheDocument();
    expect(screen.getByText("Third-party branding")).toBeInTheDocument();
    expect(screen.getByText("Documentary credibility")).toBeInTheDocument();
    expect(screen.getAllByText("Reads as expected.")).toHaveLength(9);
  });

  it("expands and counts the gates that need attention", () => {
    const failing = review({
      recommendation: "REJECT_RECOMMENDED",
      blocking_gates: ["third_party_branding"],
      uncertain_gates: ["vehicle_continuity"],
    });

    renderWithBase(<ReviewPanel review={failing} />);

    expect(screen.getByText("2 gates need attention")).toBeInTheDocument();
  });

  it("says so when nothing needs attention", () => {
    renderWithBase(<ReviewPanel review={review()} />);

    expect(screen.getByText("All nine gates")).toBeInTheDocument();
  });

  it("shows a material failure's status, codes and confidence", () => {
    const failing = review({
      recommendation: "REJECT_RECOMMENDED",
      blocking_gates: ["third_party_branding"],
      gates: {
        ...review().gates,
        third_party_branding: gate({
          status: "FAIL",
          material: true,
          codes: ["BRAND_PACKAGING_MARK"],
          confidence: 0.93,
          evidence: "A chip packet carries a readable logo.",
        }),
      },
    });

    renderWithBase(<ReviewPanel review={failing} />);

    expect(screen.getByText("Fail")).toBeInTheDocument();
    expect(screen.getByText("Material")).toBeInTheDocument();
    expect(screen.getByText("BRAND_PACKAGING_MARK")).toBeInTheDocument();
    expect(screen.getByText("confidence 0.93")).toBeInTheDocument();
    expect(screen.getByText("A chip packet carries a readable logo.")).toBeInTheDocument();
  });

  it("shows an uncertain gate without calling it a failure", () => {
    const uncertain = review({
      recommendation: "REVIEW_UNCERTAIN",
      uncertain_gates: ["third_party_branding"],
      gates: {
        ...review().gates,
        third_party_branding: gate({
          status: "UNCERTAIN",
          confidence: 0.3,
          evidence: "A sticker is below readable resolution.",
        }),
      },
    });

    renderWithBase(<ReviewPanel review={uncertain} />);

    expect(screen.getByText("Uncertain — needs your eyes")).toBeInTheDocument();
    expect(screen.getByText("Uncertain")).toBeInTheDocument();
    expect(screen.queryByText("Material")).not.toBeInTheDocument();
  });

  it("shows a not-applicable gate as neither pass nor fail", () => {
    const notApplicable = review({
      gates: {
        ...review().gates,
        vehicle_continuity: gate({
          status: "NOT_APPLICABLE",
          evidence: "No vehicle is visible.",
        }),
      },
    });

    renderWithBase(<ReviewPanel review={notApplicable} />);

    expect(screen.getByText("Not applicable")).toBeInTheDocument();
  });

  it("surfaces material drift", () => {
    const drifted = review({ material_drift: "The ute reads as an American pickup." });

    renderWithBase(<ReviewPanel review={drifted} />);

    expect(screen.getByText("The ute reads as an American pickup.")).toBeInTheDocument();
  });

  it("shows the suggested next product when the reviewer offers one", () => {
    const suggested = review({ next_hero_product: "Hoodie waist", next_camera: "Inside lift" });

    renderWithBase(<ReviewPanel review={suggested} />);

    expect(screen.getByText(/Hoodie waist — Inside lift/)).toBeInTheDocument();
  });
});

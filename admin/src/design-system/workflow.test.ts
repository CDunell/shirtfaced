import assert from "node:assert/strict";
import test from "node:test";
import type { DesignReview, HardGate, ScoreCategory } from "./domain";
import {
  HARD_GATE_IDS,
  canTransition,
  evaluateReview,
  nextStatusForReview,
} from "./workflow";

function passingGates(): HardGate[] {
  return HARD_GATE_IDS.map((id) => ({
    id,
    label: id,
    result: "pass",
    evidence: "reviewed",
  }));
}

function scoreCategories(score = 90): ScoreCategory[] {
  return [
    {
      id: "overall",
      label: "Overall",
      score,
      maximum: 100,
      minimumRequired: 70,
      notes: "",
    },
  ];
}

function review(overrides: Partial<DesignReview> = {}): DesignReview {
  return {
    id: "11111111-1111-4111-8111-111111111111",
    designId: "22222222-2222-4222-8222-222222222222",
    reviewerId: "human-reviewer",
    hardGates: passingGates(),
    scoreCategories: scoreCategories(),
    decision: "design_approved",
    rationale: "Passes the documented design gates.",
    createdAt: new Date("2026-08-07T00:00:00Z"),
    ...overrides,
  };
}

test("workflow permits intended forward transitions", () => {
  assert.equal(canTransition("draft", "brief_ready"), true);
  assert.equal(canTransition("review_ready", "design_approved"), true);
  assert.equal(canTransition("production_approved", "released"), true);
});

test("workflow blocks invalid jumps", () => {
  assert.equal(canTransition("draft", "released"), false);
  assert.equal(canTransition("brief_ready", "production_approved"), false);
  assert.equal(canTransition("released", "draft"), false);
});

test("a failed hard gate blocks approval regardless of score", () => {
  const hardGates = passingGates();
  hardGates[0] = { ...hardGates[0], result: "fail" };

  const result = evaluateReview(review({ hardGates }));

  assert.equal(result.hardGatePassed, false);
  assert.equal(result.eligibleForDesignApproval, false);
  assert.equal(nextStatusForReview(review({ hardGates })), "revision_required");
});

test("an untested hard gate blocks approval", () => {
  const hardGates = passingGates().slice(1);
  const result = evaluateReview(review({ hardGates }));

  assert.equal(result.untestedHardGates.length, 1);
  assert.equal(result.eligibleForDesignApproval, false);
});

test("a passing human review can approve design", () => {
  const candidate = review();
  const result = evaluateReview(candidate);

  assert.equal(result.eligibleForDesignApproval, true);
  assert.equal(nextStatusForReview(candidate), "design_approved");
});

test("production approval requires the higher threshold and human decision", () => {
  const candidate = review({
    decision: "production_approved",
    scoreCategories: scoreCategories(86),
  });

  const result = evaluateReview(candidate);

  assert.equal(result.eligibleForProductionApproval, true);
  assert.equal(nextStatusForReview(candidate), "production_approved");
});

test("category minimums cannot be hidden by a high total", () => {
  const candidate = review({
    scoreCategories: [
      {
        id: "composition",
        label: "Composition",
        score: 20,
        maximum: 20,
        minimumRequired: 12,
        notes: "",
      },
      {
        id: "production",
        label: "Production",
        score: 5,
        maximum: 10,
        minimumRequired: 7,
        notes: "",
      },
      {
        id: "other",
        label: "Other",
        score: 70,
        maximum: 70,
        notes: "",
      },
    ],
  });

  const result = evaluateReview(candidate);

  assert.equal(result.percentage, 95);
  assert.equal(result.failedCategoryMinimums.length, 1);
  assert.equal(result.eligibleForDesignApproval, false);
});

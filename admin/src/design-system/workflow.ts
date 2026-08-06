import type {
  DesignBrief,
  DesignReview,
  DesignStatus,
  HardGate,
  ScoreCategory,
} from "./domain";

export const HARD_GATE_IDS = [
  "product_blank_defined",
  "collection_role_defined",
  "dominant_proposition_clear",
  "thumbnail_hierarchy_survives",
  "essential_text_legible",
  "construction_conflicts_resolved",
  "production_detail_feasible",
  "identity_geometry_preserved",
  "logo_removal_recognition_survives",
  "competitor_substitution_survives",
  "worn_body_review_completed",
  "production_files_match_art",
] as const;

const ALLOWED_TRANSITIONS: Record<DesignStatus, readonly DesignStatus[]> = {
  draft: ["brief_ready", "archived"],
  brief_ready: ["artwork_in_progress", "draft", "archived"],
  artwork_in_progress: ["review_ready", "brief_ready", "archived"],
  review_ready: ["revision_required", "design_approved", "rejected"],
  revision_required: ["artwork_in_progress", "review_ready", "rejected", "archived"],
  design_approved: ["production_review", "revision_required", "archived"],
  production_review: ["production_approved", "revision_required", "rejected"],
  production_approved: ["released", "production_review", "archived"],
  released: ["archived"],
  rejected: ["artwork_in_progress", "archived"],
  archived: [],
};

export type WorkflowBlocker = {
  code: string;
  message: string;
};

export type ReviewEvaluation = {
  hardGatePassed: boolean;
  failedHardGates: HardGate[];
  untestedHardGates: HardGate[];
  totalScore: number;
  maximumScore: number;
  percentage: number;
  failedCategoryMinimums: ScoreCategory[];
  eligibleForDesignApproval: boolean;
  eligibleForProductionApproval: boolean;
};

export function canTransition(from: DesignStatus, to: DesignStatus): boolean {
  return ALLOWED_TRANSITIONS[from].includes(to);
}

export function assertTransition(from: DesignStatus, to: DesignStatus): void {
  if (!canTransition(from, to)) {
    throw new Error(`Invalid design workflow transition: ${from} -> ${to}`);
  }
}

export function validateBriefReadiness(brief: DesignBrief): WorkflowBlocker[] {
  const blockers: WorkflowBlocker[] = [];

  if (!brief.dominantProposition.trim()) {
    blockers.push({
      code: "missing_dominant_proposition",
      message: "A single dominant proposition is required.",
    });
  }

  if (!brief.canonicalBlank.trim()) {
    blockers.push({
      code: "missing_canonical_blank",
      message: "The canonical garment blank is required.",
    });
  }

  if (brief.permanentRecognitionCues.length === 0) {
    blockers.push({
      code: "missing_recognition_cue",
      message: "At least one permanent recognition cue is required.",
    });
  }

  return blockers;
}

export function evaluateReview(review: DesignReview): ReviewEvaluation {
  const gateMap = new Map(review.hardGates.map((gate) => [gate.id, gate]));
  const requiredGates = HARD_GATE_IDS.map((id) =>
    gateMap.get(id) ?? {
      id,
      label: id,
      result: "not_tested" as const,
      evidence: "",
    },
  );

  const failedHardGates = requiredGates.filter((gate) => gate.result === "fail");
  const untestedHardGates = requiredGates.filter(
    (gate) => gate.result === "not_tested",
  );
  const totalScore = review.scoreCategories.reduce(
    (total, category) => total + category.score,
    0,
  );
  const maximumScore = review.scoreCategories.reduce(
    (total, category) => total + category.maximum,
    0,
  );
  const percentage = maximumScore === 0 ? 0 : (totalScore / maximumScore) * 100;
  const failedCategoryMinimums = review.scoreCategories.filter(
    (category) =>
      category.minimumRequired !== undefined &&
      category.score < category.minimumRequired,
  );
  const hardGatePassed =
    failedHardGates.length === 0 && untestedHardGates.length === 0;

  return {
    hardGatePassed,
    failedHardGates,
    untestedHardGates,
    totalScore,
    maximumScore,
    percentage,
    failedCategoryMinimums,
    eligibleForDesignApproval:
      hardGatePassed &&
      failedCategoryMinimums.length === 0 &&
      percentage >= 75,
    eligibleForProductionApproval:
      hardGatePassed &&
      failedCategoryMinimums.length === 0 &&
      percentage >= 85 &&
      review.decision === "production_approved",
  };
}

export function nextStatusForReview(review: DesignReview): DesignStatus {
  const result = evaluateReview(review);

  if (review.decision === "rejected") return "rejected";
  if (review.decision === "archived") return "archived";
  if (!result.eligibleForDesignApproval) return "revision_required";
  if (review.decision === "production_approved") {
    return result.eligibleForProductionApproval
      ? "production_approved"
      : "revision_required";
  }
  if (review.decision === "production_review") return "production_review";
  return "design_approved";
}

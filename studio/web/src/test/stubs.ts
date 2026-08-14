/**
 * A fetch stub that routes by URL.
 *
 * The app calls several endpoints, so a single blanket stub would make tests lie
 * about which one produced a result.
 */

import { vi } from "vitest";

import type {
  Attempt,
  GateName,
  GateResult,
  CanonProposal,
  DecisionResult,
  DecisionSummary,
  GenerationResult,
  NextShot,
  PlanPreview,
  Review,
  Shot,
  WorldDetail,
  WorldSummary,
} from "../api/client";
import type { ConceptDetailView, ConceptView, DesignAttemptView } from "../api/concepts";

export const HEALTH = { status: "ok", version: "0.1.0" };

export function shot(overrides: Partial<Shot> = {}): Shot {
  return {
    id: overrides.external_id ?? "shot-1",
    external_id: "W01-011",
    sequence: 11,
    priority: 100,
    title: "Car interior transition",
    hero_product: "Tote bag",
    camera_position: "Rear seat",
    lighting_source: null,
    status: "planned",
    disabled: false,
    source_line: 33,
    ...overrides,
  };
}

export const WORLD_SUMMARY: WorldSummary = {
  id: "world-1",
  slug: "world-01",
  name: "SHIRTFACED — WORLD 01",
  status: "active",
  world_document_hash: "a".repeat(64),
  continuity_document_hash: "b".repeat(64),
  shotlist_document_hash: "c".repeat(64),
};

export function worldDetail(overrides: Partial<WorldDetail> = {}): WorldDetail {
  const shots = overrides.shots ?? [
    shot({
      id: "s1",
      external_id: "W01-001",
      sequence: 1,
      title: "Walking between venues",
      status: "approved",
    }),
    shot({
      id: "s2",
      external_id: "W01-008",
      sequence: 8,
      title: "Bottle shop after close",
      status: "rejected",
    }),
    shot({ id: "s3", external_id: "W01-011", sequence: 11 }),
  ];

  return {
    ...WORLD_SUMMARY,
    shots,
    counts: {
      total: shots.length,
      planned: shots.filter((s) => s.status === "planned").length,
      in_progress: 0,
      approved: shots.filter((s) => s.status === "approved").length,
      rejected: shots.filter((s) => s.status === "rejected").length,
      abandoned: 0,
    },
    next_planned_shot: shots.find((s) => s.status === "planned") ?? null,
    ...overrides,
  };
}

export function nextShot(overrides: Partial<NextShot> = {}): NextShot {
  return {
    selected: shot(),
    reason:
      "W01-011 chosen from 2 eligible planned shots. Lowest priority (100), then sequence (11).",
    eligible_count: 2,
    set_aside: [{ external_id: "W01-001", reason: "already approved" }],
    last_hero_product: "Cap",
    last_camera_position: "Beside parked car",
    ...overrides,
  };
}

export function planPreview(overrides: Partial<PlanPreview> = {}): PlanPreview {
  return {
    shot: shot(),
    selection_reason: "W01-011 chosen from 2 eligible planned shots.",
    plan: {
      scene_summary: "Car interior transition",
      emotional_beat: "Renewed momentum",
      hero_product: "Tote bag",
      product_visibility_instruction: "Visible because it is being moved.",
      camera_position: "Rear seat",
      lighting_source: "Interior dome light",
      documentary_imperfection: "The door frame crops the edge.",
      australian_authenticity_anchors: ["Suburban Australian street"],
      negative_constraints: ["No visible branding"],
      selection_rationale: "Next planned shot.",
      production_prompt: "Documentary 35mm photograph of friends reorganising a car.",
    },
    live: false,
    ...overrides,
  };
}

const GATE_NAMES: GateName[] = [
  "mood",
  "australian_authenticity",
  "product_visibility",
  "third_party_branding",
  "vehicle_continuity",
  "wardrobe_balance",
  "composition",
  "documentary_credibility",
  "story",
];

export function gate(overrides: Partial<GateResult> = {}): GateResult {
  return {
    status: "PASS",
    evidence: "Reads as expected.",
    codes: [],
    confidence: 0.85,
    material: false,
    ...overrides,
  };
}

export function review(overrides: Partial<Review> = {}): Review {
  const gates = Object.fromEntries(GATE_NAMES.map((name) => [name, gate()])) as Record<
    GateName,
    GateResult
  >;

  return {
    id: "review-1",
    review_model: "fake-review-model",
    recommendation: "APPROVE_RECOMMENDED",
    verdict: "approved",
    gates,
    mood_score: 4,
    australian_authenticity_score: 4,
    product_visibility_score: 4,
    documentary_credibility_score: 4,
    story_score: 4,
    branding_compliant: true,
    vehicle_compliant: true,
    strongest_success: "The moment reads as taken rather than arranged.",
    material_drift: null,
    recommended_action: "APPROVE_RECOMMENDED",
    next_hero_product: null,
    next_camera: null,
    created_at: "2026-08-05T00:00:00Z",
    blocking_gates: [],
    uncertain_gates: [],
    ...overrides,
  };
}

export function attempt(overrides: Partial<Attempt> = {}): Attempt {
  return {
    id: "attempt-1",
    attempt_number: 1,
    // Generate and review both run, so an attempt comes to rest here.
    state: "awaiting_decision",
    shot: shot(),
    selection_reason: "W01-011 chosen from 2 eligible planned shots.",
    production_prompt: "Documentary 35mm photograph of friends reorganising a car.",
    prompt_plan: null,
    image_model: "a-test-model",
    image_size: "1536x1024",
    image_quality: "high",
    provider_request_id: "req-1",
    hero_product: "Tote bag",
    camera_position: "Rear seat",
    world_document_hash: "a".repeat(64),
    shotlist_document_hash: "c".repeat(64),
    failure_code: null,
    failure_message: null,
    parent_attempt_id: null,
    created_at: "2026-08-05T00:00:00Z",
    image_url: "/assets/asset-1",
    thumbnail_url: "/assets/asset-2",
    review: review(),
    decision: null,
    approved: false,
    ...overrides,
  };
}

export function decisionSummary(overrides: Partial<DecisionSummary> = {}): DecisionSummary {
  return {
    decision: "approved",
    reason: null,
    note: null,
    instruction: null,
    promote_to_reference: false,
    markdown_sync: "succeeded",
    git_sync: "succeeded",
    git_commit: "abc123",
    reconciliation_required: false,
    reconciliation_detail: null,
    created_at: "2026-08-05T00:00:00Z",
    ...overrides,
  };
}

export function decisionResult(overrides: Partial<DecisionResult> = {}): DecisionResult {
  return {
    attempt_id: "attempt-1",
    attempt_state: "approved",
    decision: "approved",
    shot_external_id: "W01-011",
    shot_status: "approved",
    reason: null,
    note: null,
    instruction: null,
    promote_to_reference: false,
    markdown_sync: "succeeded",
    git_sync: "succeeded",
    reference_sync: "not_attempted",
    git_commit: "abc123",
    document_hashes: {},
    reconciliation_required: false,
    reconciliation: [],
    ...overrides,
  };
}

export function generationResult(overrides: Partial<GenerationResult> = {}): GenerationResult {
  return { attempt: attempt(), review: review(), live: false, review_live: false, ...overrides };
}

export function canonProposal(overrides: Partial<CanonProposal> = {}): CanonProposal {
  return {
    id: "proposal-1",
    status: "pending",
    proposed_text: "Every ute must show an open aluminium alloy tray.",
    reason: "The ute read as an American pickup.",
    human_note: null,
    classification: null,
    classification_reason: null,
    classified_by: null,
    target_heading: null,
    reviewer_model: "fake-review-model",
    applied_wording: null,
    applied_at: null,
    failure_detail: null,
    git_commit: null,
    created_at: "2026-08-05T00:00:00Z",
    decided_at: null,
    allowed_headings: ["Wardrobe", "Composition", "Product Rotation & Vehicle Canon"],
    ...overrides,
  };
}

export function proposalDiff() {
  return {
    proposal_id: "proposal-1",
    target_heading: "Wardrobe",
    unified_diff:
      "--- WORLD.md (current)\n+++ WORLD.md (proposed)\n+Every ute must show an open aluminium alloy tray.",
    applied_wording: "Every ute must show an open aluminium alloy tray.",
  };
}

export function conceptView(overrides: Partial<ConceptView> = {}): ConceptView {
  return {
    id: "concept-1",
    library: "tshirt",
    external_number: 1,
    slug: "001-absolute-weapon",
    title: "ABSOLUTE WEAPON",
    concept_text:
      "Museum-quality portrait treatment of a pedestal fan. ABSOLUTE WEAPON. No explanation.",
    status: "backlog",
    concept_kind: "other",
    retirement: "",
    salvage: "",
    garments: [],
    round: 1,
    round_label: "Round 01",
    priority: 0,
    tags: [],
    treatment_lanes: [],
    notes: "",
    attempt_count: 0,
    latest_attempt_state: null,
    approved_versions: 0,
    ...overrides,
  };
}

export function conceptDetailView(overrides: Partial<ConceptDetailView> = {}): ConceptDetailView {
  return {
    ...conceptView(),
    attempts: [],
    versions: [],
    ...overrides,
  };
}

/* --- The scorecard -----------------------------------------------------------
 *
 * Deliberately small: three gates and two categories rather than the real
 * thirteen and nine. The panel renders whatever the rubric endpoint sends, so
 * a stub that mirrored the full rubric would be testing the fixture rather
 * than the screen -- and would have to be edited every time the scorecard
 * changed, which is exactly the second copy the port removed.
 */

export const RUBRIC = {
  groups: [
    { id: "validate_recognition", label: "Validate recognition", blurb: "Constitution step 7." },
    { id: "validate_production", label: "Validate production", blurb: "Constitution step 8." },
    {
      id: "review_against_collection",
      label: "Review against the collection",
      blurb: "Constitution step 9.",
    },
  ],
  gates: [
    {
      id: "dominant_proposition_clear",
      label: "Dominant proposition is clear",
      question: "Within three seconds, is the main visual idea identifiable?",
      group: "validate_recognition",
    },
    {
      id: "product_blank_defined",
      label: "Product and blank defined",
      question: "Is the garment, blank, fit, colour and production method decided?",
      group: "validate_production",
    },
    {
      id: "rights_cleared_for_sale",
      label: "Rights cleared for sale",
      question: "Are the rights to every source cleared for sale?",
      group: "review_against_collection",
    },
  ],
  categories: [
    {
      id: "dominant_proposition",
      label: "Dominant Proposition",
      prompt: "One clear primary idea.",
      maximum: 10,
      ratingFloor: 4,
      minimumRequired: 8,
      group: "validate_recognition",
    },
    {
      id: "production_integrity",
      label: "Production Integrity",
      prompt: "Line and gap integrity.",
      maximum: 15,
      ratingFloor: 4,
      minimumRequired: 12,
      group: "validate_production",
    },
  ],
  ratingMeanings: [
    "absent or structurally failed",
    "materially weak",
    "below release standard",
    "competent and acceptable",
    "strong",
    "exceptional and clearly intentional",
  ],
  approvalPercentage: 75,
  productionPercentage: 85,
};

/** One work row. Defaults to the case that matters: something waiting on a
 * person, with a sentence saying what to do about it. */
export function workItem(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    concept_id: "concept-1",
    library: "tshirt",
    external_number: 1,
    title: "ABSOLUTE WEAPON",
    concept_status: "exploring",
    research_run_id: "",
    research_concept_number: null,
    attempt_id: "attempt-1",
    attempt_number: 1,
    attempt_state: "awaiting_decision",
    has_artwork: true,
    percentage: 80,
    eligible: true,
    blockers: [],
    approved_version: null,
    approved_design_id: null,
    stage: "awaiting_decision",
    next_action:
      "Passed at 80/100 with no failed gates. Approve it, or send it back with a reason.",
    ...overrides,
  };
}

/** A brief with nothing chosen: the state that blocks an attempt. */
export function briefView(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    concept_id: "concept-1",
    garment_category: "",
    canonical_blank: "",
    fit_block: "",
    fabric_weight: "",
    garment_colour: "",
    wash: "",
    production_method: "",
    intended_use: "",
    commercial_tier: "",
    target_release: "",
    collection_role: null,
    graphic_archetype: null,
    layout_archetype: null,
    archetype_departure_reason: "",
    zones: {},
    typography: {},
    advisor_snapshot: {},
    notes: "",
    ready_for_artwork: false,
    next_action:
      "Choose a collection role and a graphic archetype. The constitution decides what a " +
      "product is before any artwork exists, and an attempt cannot open without them.",
    ...overrides,
  };
}

/** What leaves the building with an attempt. */
export const BRIEF_PACKAGE = {
  text: [
    "SECOND BREAKFAST — Shirtfaced concept #1",
    "",
    "A type-led chest lockup.",
    "",
    "EVIDENCE",
    "2 reference image(s) from the vintage corpus.",
  ].join("\n"),
  evidence_images: ["listing-1/0.jpg", "listing-1/2.jpg"],
  evidence_listing_ids: ["listing-1"],
  research_run_id: "run-9",
  evidence_count: 2,
};

export const ADVICE = {
  input: "3 words, with a graphic",
  intent: "both",
  tradition: "novelty",
  recommendations: [
    {
      field: "scale_role",
      value: "S2 emblem",
      evidence: "median coverage 8.1% across 412 measured images",
      confidence: "corpus",
    },
  ],
  alternatives: ["S1 chest identifier"],
  not_decided: ["subject matter"],
};

export const GARMENTS = {
  garment_tee_crew_front: [{ key: "centre_chest", width_mm: 279.4, height_mm: 279.4 }],
};

/** A review that blocks, which is the honest default: nothing answered yet. */
export function reviewView(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    attempt_id: "attempt-1",
    reviewer: "",
    gates: RUBRIC.gates.map((gate) => ({
      id: gate.id,
      label: gate.label,
      // The two the brief answers arrive already decided, with their evidence.
      result: gate.id === "product_blank_defined" ? "fail" : "not_tested",
      evidence:
        gate.id === "product_blank_defined" ? "the brief does not state the canonical blank" : "",
    })),
    categories: [],
    rationale: "",
    decision: "design_approved",
    measurements: {},
    evaluation: {
      hardGatePassed: false,
      failedHardGates: [],
      untestedHardGates: RUBRIC.gates.map((gate) => ({
        id: gate.id,
        label: gate.label,
        result: "not_tested",
        evidence: "",
      })),
      totalScore: 0,
      maximumScore: 0,
      percentage: 0,
      failedCategoryMinimums: [],
      unratedCategories: ["dominant_proposition", "production_integrity"],
      eligibleForDesignApproval: false,
      eligibleForProductionApproval: false,
      band: "reject_or_rebuild",
      bandLabel: "Reject or rebuild",
      blockers: ["3 gates not answered", "2 categories not rated"],
    },
    frozen: false,
    // The brief answers these two; the panel shows them as facts rather than
    // offering them as choices.
    derived_gates: ["product_blank_defined", "collection_role_defined"],
    next_action: "Artwork attached. Measure it, then answer the gates and rate the categories.",
    ...overrides,
  };
}

export function designAttemptView(overrides: Partial<DesignAttemptView> = {}): DesignAttemptView {
  return {
    id: "attempt-1",
    concept_id: "concept-1",
    attempt_number: 1,
    method: "manual_import",
    state: "awaiting_decision",
    parent_attempt_id: null,
    created_at: "2026-08-12T00:00:00Z",
    assets: [],
    decision: null,
    approved_version: null,
    ...overrides,
  };
}

export interface Routes {
  health?: unknown;
  worlds?: unknown;
  world?: unknown;
  worldStatus?: number;
  nextShot?: unknown;
  planPreview?: unknown;
  planStatus?: number;
  planDetail?: string;
  attempts?: unknown;
  decision?: unknown;
  decisionStatus?: number;
  decisionDetail?: string;
  proposals?: unknown;
  proposalDiff?: unknown;
  proposalStatus?: number;
  proposalDetail?: string;
  generation?: unknown;
  generationStatus?: number;
  generationDetail?: string;
  concepts?: unknown;
  conceptDetail?: unknown;
  conceptNext?: unknown;
  conceptQueue?: unknown;
  conceptAction?: unknown;
  conceptActionStatus?: number;
  conceptActionDetail?: string;
  work?: unknown;
  brief?: unknown;
  briefPackage?: unknown;
  advice?: unknown;
  rubric?: unknown;
  attemptReview?: unknown;
  garments?: unknown;
}

/** Install a fetch stub answering the endpoints the app uses. */
export function stubApi(routes: Routes = {}): ReturnType<typeof vi.fn> {
  const spy = vi.fn((input: string) => {
    if (input.startsWith("/health")) {
      return Promise.resolve(new Response(JSON.stringify(routes.health ?? HEALTH)));
    }
    if (input === "/api/worlds") {
      return Promise.resolve(new Response(JSON.stringify(routes.worlds ?? [WORLD_SUMMARY])));
    }
    // Before the generic /attempts and /decision branches below: concept URLs
    // share those suffixes, and ordering decides which handler answers.
    if (input === "/api/design/advise") {
      return Promise.resolve(new Response(JSON.stringify(routes.advice ?? ADVICE)));
    }
    if (input.startsWith("/api/concepts")) {
      // Before the /attempts branch: the scorecard endpoints share that path.
      if (input.includes("/brief-package")) {
        return Promise.resolve(new Response(JSON.stringify(routes.briefPackage ?? BRIEF_PACKAGE)));
      }
      if (input.includes("/brief-taken")) {
        return Promise.resolve(
          new Response(JSON.stringify({ taken_at: "now", evidence_count: 2 })),
        );
      }
      if (input.endsWith("/brief")) {
        return Promise.resolve(new Response(JSON.stringify(routes.brief ?? briefView())));
      }
      if (input === "/api/concepts/work" || input.startsWith("/api/concepts/work?")) {
        return Promise.resolve(new Response(JSON.stringify(routes.work ?? [])));
      }
      if (input === "/api/concepts/rubric") {
        return Promise.resolve(new Response(JSON.stringify(routes.rubric ?? RUBRIC)));
      }
      if (input === "/api/concepts/garments") {
        return Promise.resolve(new Response(JSON.stringify(routes.garments ?? GARMENTS)));
      }
      if (input.includes("/review") || input.includes("/measure")) {
        return Promise.resolve(new Response(JSON.stringify(routes.attemptReview ?? reviewView())));
      }
      if (input === "/api/concepts/queue") {
        return Promise.resolve(new Response(JSON.stringify(routes.conceptQueue ?? [])));
      }
      if (input === "/api/concepts/next") {
        if (routes.conceptNext === undefined) {
          return Promise.resolve(
            new Response(JSON.stringify({ detail: "no concept is ready" }), { status: 404 }),
          );
        }
        return Promise.resolve(new Response(JSON.stringify(routes.conceptNext)));
      }
      if (input.startsWith("/api/concepts/attempts/")) {
        const actionStatus = routes.conceptActionStatus ?? 200;
        if (actionStatus >= 400) {
          return Promise.resolve(
            new Response(JSON.stringify({ detail: routes.conceptActionDetail ?? "refused" }), {
              status: actionStatus,
            }),
          );
        }
        return Promise.resolve(new Response(JSON.stringify(routes.conceptAction ?? {})));
      }
      if (input === "/api/concepts" || input.startsWith("/api/concepts?")) {
        return Promise.resolve(new Response(JSON.stringify(routes.concepts ?? [])));
      }
      return Promise.resolve(
        new Response(JSON.stringify(routes.conceptDetail ?? conceptDetailView())),
      );
    }
    if (input.endsWith("/attempts")) {
      return Promise.resolve(new Response(JSON.stringify(routes.attempts ?? [])));
    }
    if (input.endsWith("/continue")) {
      const generationStatus = routes.generationStatus ?? 201;
      if (generationStatus >= 400) {
        return Promise.resolve(
          new Response(JSON.stringify({ detail: routes.generationDetail ?? "refused" }), {
            status: generationStatus,
          }),
        );
      }
      return Promise.resolve(new Response(JSON.stringify(routes.generation ?? generationResult())));
    }
    // Before the decision branch: a canon-proposal URL also ends with /reject
    // and /approve, so ordering decides which handler answers it.
    if (input.includes("/canon-proposals")) {
      const isAction =
        input.includes("/diff") ||
        input.endsWith("/classify") ||
        input.endsWith("/approve") ||
        input.endsWith("/reject");
      const proposalStatus = routes.proposalStatus ?? 200;

      // The failure status applies to actions only. A listing that also failed would
      // render nothing, so a test could not reach the control it means to exercise.
      if (isAction && proposalStatus >= 400) {
        return Promise.resolve(
          new Response(JSON.stringify({ detail: routes.proposalDetail ?? "refused" }), {
            status: proposalStatus,
          }),
        );
      }
      if (input.includes("/diff")) {
        return Promise.resolve(new Response(JSON.stringify(routes.proposalDiff ?? proposalDiff())));
      }
      if (isAction) {
        return Promise.resolve(new Response(JSON.stringify(canonProposal())));
      }
      return Promise.resolve(new Response(JSON.stringify(routes.proposals ?? [])));
    }
    if (input.endsWith("/approve") || input.endsWith("/reject") || input.endsWith("/variation")) {
      const decisionStatus = routes.decisionStatus ?? 200;
      if (decisionStatus >= 400) {
        return Promise.resolve(
          new Response(JSON.stringify({ detail: routes.decisionDetail ?? "refused" }), {
            status: decisionStatus,
          }),
        );
      }
      return Promise.resolve(new Response(JSON.stringify(routes.decision ?? decisionResult())));
    }
    if (input.endsWith("/next-shot")) {
      return Promise.resolve(new Response(JSON.stringify(routes.nextShot ?? nextShot())));
    }
    if (input.endsWith("/plan-preview")) {
      const planStatus = routes.planStatus ?? 200;
      if (planStatus !== 200) {
        return Promise.resolve(
          new Response(JSON.stringify({ detail: routes.planDetail ?? "refused" }), {
            status: planStatus,
          }),
        );
      }
      return Promise.resolve(new Response(JSON.stringify(routes.planPreview ?? planPreview())));
    }
    if (input.startsWith("/api/worlds/")) {
      const status = routes.worldStatus ?? 200;
      if (status !== 200) {
        return Promise.resolve(new Response("nope", { status }));
      }
      return Promise.resolve(new Response(JSON.stringify(routes.world ?? worldDetail())));
    }
    return Promise.resolve(new Response("not found", { status: 404 }));
  });

  vi.stubGlobal("fetch", spy);
  return spy;
}

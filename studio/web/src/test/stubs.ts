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
  GenerationResult,
  NextShot,
  PlanPreview,
  Review,
  Shot,
  WorldDetail,
  WorldSummary,
} from "../api/client";

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
    state: "generated",
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
    approved: false,
    ...overrides,
  };
}

export function generationResult(overrides: Partial<GenerationResult> = {}): GenerationResult {
  return { attempt: attempt(), review: review(), live: false, review_live: false, ...overrides };
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
  generation?: unknown;
  generationStatus?: number;
  generationDetail?: string;
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

/**
 * A fetch stub that routes by URL.
 *
 * The app calls several endpoints, so a single blanket stub would make tests lie
 * about which one produced a result.
 */

import { vi } from "vitest";

import type { NextShot, PlanPreview, Shot, WorldDetail, WorldSummary } from "../api/client";

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

export interface Routes {
  health?: unknown;
  worlds?: unknown;
  world?: unknown;
  worldStatus?: number;
  nextShot?: unknown;
  planPreview?: unknown;
  planStatus?: number;
  planDetail?: string;
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

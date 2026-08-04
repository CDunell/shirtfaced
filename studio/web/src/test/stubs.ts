/**
 * A fetch stub that routes by URL.
 *
 * The app calls several endpoints, so a single blanket stub would make tests lie
 * about which one produced a result.
 */

import { vi } from "vitest";

import type { Shot, WorldDetail, WorldSummary } from "../api/client";

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

export interface Routes {
  health?: unknown;
  worlds?: unknown;
  world?: unknown;
  worldStatus?: number;
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

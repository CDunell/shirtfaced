/**
 * Pure mapping logic for sync-approved-designs.ts, pulled out of that script
 * so it can be unit tested without a live connection to either database.
 */
import type { Category } from "./schema";

// Studio's garments field is free-text per concept, not this admin's fixed
// CATEGORIES enum — best-effort mapping, defaulting to "tees" (the locked
// main range per GARMENT_BLANK_STRATEGY.md) rather than guessing wrong.
const GARMENT_CATEGORY: Record<string, Category> = {
  tee: "tees",
  "t-shirt": "tees",
  tshirt: "tees",
  tank: "tanks",
  singlet: "tanks",
  hoodie: "hoodies",
  sweatshirt: "hoodies",
  hat: "hats",
  cap: "hats",
  beanie: "hats",
};

export function categoryFor(garments: string[] | null | undefined): Category {
  for (const garment of garments ?? []) {
    const hit = GARMENT_CATEGORY[garment.toLowerCase().trim()];
    if (hit) return hit;
  }
  return "tees";
}

export function firstSentence(text: string | null | undefined): string {
  const trimmed = (text ?? "").trim();
  const cut = trimmed.search(/(?<=[.!?])\s/);
  return cut === -1 ? trimmed.slice(0, 140) : trimmed.slice(0, cut);
}

export function slugFor(conceptSlug: string): string {
  return `studio-${conceptSlug}`;
}

export function garmentColourFor(productionSpec: Record<string, unknown> | null | undefined): string {
  const colour = productionSpec?.garment_colour;
  return typeof colour === "string" && /^#[0-9a-fA-F]{6}$/.test(colour) ? colour : "#1c1c1a";
}

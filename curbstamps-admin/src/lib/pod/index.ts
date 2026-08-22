import type { PodProvider } from "./types";
import { MockPodProvider } from "./mock-adapter";
import { PrintfulProvider } from "./printful-adapter";
import { PrintifyProvider } from "./printify-adapter";

export * from "./types";

let cached: PodProvider | null = null;

/**
 * POD_PROVIDER selects the adapter — unset or "mock" is the only one safe
 * to run without any vendor account. "printify" is the decided provider
 * (see docs/curbstamps/CURB_STAMPS_SPEC.md §4) — set it only once
 * PRINTIFY_API_KEY/PRINTIFY_SHOP_ID are set AND printify-adapter.ts's
 * SYNC_VARIANT_MAP is filled in for the products actually being sold, or
 * every real order will fail loudly at the POD step (see markOrderPaid in
 * db/store-queries.ts, which records that failure on the order rather than
 * losing it silently). "printful" stays available as a working alternative.
 */
export function getPodProvider(): PodProvider {
  if (cached) return cached;
  const which = process.env.POD_PROVIDER || "mock";
  cached = which === "printify" ? new PrintifyProvider() : which === "printful" ? new PrintfulProvider() : new MockPodProvider();
  return cached;
}

import type { PodProvider } from "./types";
import { MockPodProvider } from "./mock-adapter";
import { PrintfulProvider } from "./printful-adapter";

export * from "./types";

let cached: PodProvider | null = null;

/**
 * POD_PROVIDER selects the adapter — unset or "mock" (the default) is the
 * only one safe to run without any vendor account. Set to "printful" only
 * once PRINTFUL_API_KEY is set AND printful-adapter.ts's SYNC_VARIANT_MAP is
 * filled in for the products actually being sold, or every real order will
 * fail loudly at the POD step (see markOrderPaid in db/store-queries.ts,
 * which records that failure on the order rather than losing it silently).
 */
export function getPodProvider(): PodProvider {
  if (cached) return cached;
  const which = process.env.POD_PROVIDER || "mock";
  cached = which === "printful" ? new PrintfulProvider() : new MockPodProvider();
  return cached;
}

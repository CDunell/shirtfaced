import type { PodProvider } from "./types";
import { MockPodProvider } from "./mock-adapter";
import { PrintfulProvider } from "./printful-adapter";
import { PrintifyProvider } from "./printify-adapter";

export * from "./types";

let cached: PodProvider | null = null;

/**
 * POD_PROVIDER selects the adapter — unset or "mock" (the default) is the
 * only one safe to run without any vendor account.
 *
 * "printify" is the one with a real, live catalog behind it (shop 28675131,
 * built for the tee category — see docs/curbstamps) and just needs
 * PRINTIFY_API_TOKEN + PRINTIFY_SHOP_ID set. It still requires manual
 * verification against a real test order before trusting it unattended —
 * see printify-adapter.ts's own comment on why createOrder() stops short of
 * sending anything to production.
 *
 * "printful" is a reference implementation only — printful-adapter.ts's
 * SYNC_VARIANT_MAP is empty and there's no Printful catalog built, so it
 * will fail loudly at the POD step the moment it's selected (see
 * markOrderPaid in db/store-queries.ts, which records that failure on the
 * order rather than losing it silently).
 */
export function getPodProvider(): PodProvider {
  if (cached) return cached;
  const which = process.env.POD_PROVIDER || "mock";
  cached =
    which === "printify" ? new PrintifyProvider() : which === "printful" ? new PrintfulProvider() : new MockPodProvider();
  return cached;
}

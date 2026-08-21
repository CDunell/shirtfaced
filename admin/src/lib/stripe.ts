import Stripe from "stripe";

/**
 * Null when STRIPE_SECRET_KEY isn't set on this app (a separate env var from
 * the storefront's own — same live key, two apps) — callers treat that as
 * "refunds aren't available yet" rather than crashing.
 */
export function getStripe(): Stripe | null {
  const key = process.env.STRIPE_SECRET_KEY;
  return key ? new Stripe(key) : null;
}

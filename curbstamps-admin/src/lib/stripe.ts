import Stripe from "stripe";

/** Null when STRIPE_SECRET_KEY isn't set — callers treat that as "not
 * available yet" rather than crashing. Same key as curbstamps-site's own
 * STRIPE_SECRET_KEY, set separately here for refunds initiated from this
 * app (see actions.ts). */
export function getStripe(): Stripe | null {
  const key = process.env.STRIPE_SECRET_KEY;
  return key ? new Stripe(key) : null;
}

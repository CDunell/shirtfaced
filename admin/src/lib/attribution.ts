/**
 * Shape of the storefront's captured attribution (src/lib/attribution.ts in
 * the root app), stored verbatim as the orders.attribution jsonb column —
 * duplicated here rather than shared across the two separate Next.js apps.
 */
export type AttributionTouch = {
  at: string;
  landingPath: string;
  referrer: string;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_content?: string;
  utm_term?: string;
  fbclid?: string;
  ttclid?: string;
  gclid?: string;
  gbraid?: string;
  wbraid?: string;
  epik?: string;
  msclkid?: string;
};

export type Attribution = {
  version: 1;
  first: AttributionTouch;
  last: AttributionTouch;
};

/** First-touch source/medium as one display string, e.g.
 * "instagram/paid_social". Null if the order has no attribution at all. */
export function channelFromAttribution(attribution: unknown): string | null {
  if (!attribution || typeof attribution !== "object") return null;
  const first = (attribution as Partial<Attribution>).first;
  if (!first) return null;
  const source = first.utm_source;
  const medium = first.utm_medium;
  if (source && medium) return `${source}/${medium}`;
  return source ?? medium ?? null;
}

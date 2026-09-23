export function formatCents(cents: number): string {
  return new Intl.NumberFormat("en-AU", {
    style: "currency",
    currency: "AUD",
  }).format(cents / 100);
}

/** For values that are already in dollars (ad-platform APIs report spend
 * and conversion value in whole currency units, not cents) — see
 * lib/analytics-reporting.ts. */
export function formatDollars(value: number): string {
  return new Intl.NumberFormat("en-AU", {
    style: "currency",
    currency: "AUD",
  }).format(value);
}

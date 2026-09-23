/** One colour per data source across every analytics chart, so the same
 * platform reads the same colour everywhere on the dashboard. */
export const CHANNEL_COLORS = {
  revenue: "#c6ff33", // real order revenue (internal) — the brand accent, the "what actually happened" line
  meta: "#ff3c8e",
  tiktok: "#ff4d4d",
  googleAds: "#ff6a00",
  ga4: "#297bff",
} as const;

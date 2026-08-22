declare global {
  interface Window {
    ttq?: {
      track: (
        event: string,
        properties?: Record<string, unknown>,
        options?: { event_id?: string },
      ) => void;
    };
  }
}

/**
 * Client half of Purchase tracking, fired from checkout/success. Shares
 * event_id with the server-side call in src/lib/tiktok-events.ts (both use
 * the order id) so TikTok dedupes the pair into one conversion instead of
 * counting the sale twice.
 */
export function trackTikTokPurchase(orderId: string, valueDollars: number) {
  window.ttq?.track(
    "CompletePayment",
    { value: valueDollars, currency: "AUD" },
    { event_id: orderId },
  );
}

/**
 * Cross-channel conversion tracking. Fires into whichever of GA4 / Meta
 * Pixel / TikTok Pixel are actually configured (see Analytics.tsx for the
 * scripts that put gtag/fbq/ttq on window) — a platform with no env var set
 * never got its script loaded, so its call here is just a no-op.
 *
 * The Meta and TikTok calls pass transactionId as their event ID, matching
 * the event_id the server-side Conversions/Events API call uses for the same
 * order (src/lib/server-analytics.ts, called from the Stripe webhook) — that
 * shared ID is what lets each platform dedupe the client and server fires
 * into one conversion instead of counting the sale twice.
 */

const GOOGLE_ADS_ID = process.env.NEXT_PUBLIC_GOOGLE_ADS_ID;
const GOOGLE_ADS_PURCHASE_LABEL = process.env.NEXT_PUBLIC_GOOGLE_ADS_PURCHASE_LABEL;

declare global {
  interface Window {
    gtag?: (...args: unknown[]) => void;
    fbq?: (...args: unknown[]) => void;
    ttq?: {
      track: (
        event: string,
        params?: Record<string, unknown>,
        options?: { event_id: string },
      ) => void;
    };
  }
}

export type PurchaseItem = {
  id: string;
  name: string;
  price: number;
  quantity: number;
  variant: string;
};

export type Purchase = {
  transactionId: string;
  value: number;
  currency: "AUD";
  items: PurchaseItem[];
};

export function trackPurchase(purchase: Purchase) {
  if (typeof window === "undefined") return;

  window.gtag?.("event", "purchase", {
    transaction_id: purchase.transactionId,
    value: purchase.value,
    currency: purchase.currency,
    items: purchase.items.map((item) => ({
      item_id: item.id,
      item_name: item.name,
      item_variant: item.variant,
      price: item.price,
      quantity: item.quantity,
    })),
  });

  // Google Ads' own Purchase conversion action — separate from the GA4
  // 'purchase' event above, and only fires if both id and label are set
  // (Ads needs its own conversion action configured, GA4 config alone
  // doesn't cover this).
  if (GOOGLE_ADS_ID && GOOGLE_ADS_PURCHASE_LABEL) {
    window.gtag?.("event", "conversion", {
      send_to: `${GOOGLE_ADS_ID}/${GOOGLE_ADS_PURCHASE_LABEL}`,
      value: purchase.value,
      currency: purchase.currency,
      transaction_id: purchase.transactionId,
    });
  }

  window.fbq?.(
    "track",
    "Purchase",
    {
      value: purchase.value,
      currency: purchase.currency,
      contents: purchase.items.map((item) => ({
        id: item.id,
        quantity: item.quantity,
        item_price: item.price,
      })),
      content_type: "product",
    },
    { eventID: purchase.transactionId },
  );

  window.ttq?.track(
    "CompletePayment",
    {
      value: purchase.value,
      currency: purchase.currency,
      contents: purchase.items.map((item) => ({
        content_id: item.id,
        content_name: item.name,
        quantity: item.quantity,
        price: item.price,
      })),
    },
    { event_id: purchase.transactionId },
  );
}

/** Guards against firing the same order twice — see the two call sites in
 * checkout (inline confirm vs. redirect-back) in PaymentStep.tsx and
 * checkout/success/page.tsx. */
export function hasTrackedPurchase(transactionId: string) {
  try {
    return window.sessionStorage.getItem(`sf-purchase-tracked:${transactionId}`) === "1";
  } catch {
    return false;
  }
}

export function markPurchaseTracked(transactionId: string) {
  try {
    window.sessionStorage.setItem(`sf-purchase-tracked:${transactionId}`, "1");
  } catch {
    // sessionStorage unavailable (private mode, etc.) — worst case a refresh
    // could double-count one order client-side; not worth failing the page over
  }
}

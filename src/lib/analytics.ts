/**
 * Cross-channel conversion tracking. Fires into whichever of GA4 / Meta
 * Pixel / TikTok Pixel are actually configured (see Analytics.tsx for the
 * scripts that put gtag/fbq/ttq on window) — a platform with no env var set
 * never got its script loaded, so its call here is just a no-op.
 */

declare global {
  interface Window {
    gtag?: (...args: unknown[]) => void;
    fbq?: (...args: unknown[]) => void;
    ttq?: { track: (event: string, params?: Record<string, unknown>) => void };
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

  window.fbq?.("track", "Purchase", {
    value: purchase.value,
    currency: purchase.currency,
    contents: purchase.items.map((item) => ({
      id: item.id,
      quantity: item.quantity,
      item_price: item.price,
    })),
    content_type: "product",
  });

  window.ttq?.track("CompletePayment", {
    value: purchase.value,
    currency: purchase.currency,
    contents: purchase.items.map((item) => ({
      content_id: item.id,
      content_name: item.name,
      quantity: item.quantity,
      price: item.price,
    })),
  });
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

import { createHash } from "node:crypto";

/**
 * Server-side half of purchase tracking — Meta Conversions API and TikTok
 * Events API, called from the Stripe webhook (src/app/api/stripe-webhook)
 * once payment has actually settled. Exists alongside the client-side pixel
 * fires in src/lib/analytics.ts, not instead of them: Safari's ITP and ad
 * blockers silently drop a real share of client-only pixel events, so ad
 * platforms count on a matching server event to fill the gap. Sharing the
 * same event_id (the orderId) across both is what lets each platform
 * deduplicate the pair into a single conversion instead of double-counting.
 *
 * Each call is a no-op if its access token isn't configured, same
 * "unset means quietly absent" convention as the rest of this app's
 * integrations — see .env.example.
 */

const META_PIXEL_ID = process.env.NEXT_PUBLIC_META_PIXEL_ID;
const META_ACCESS_TOKEN = process.env.META_CONVERSIONS_API_ACCESS_TOKEN;
const TIKTOK_PIXEL_ID = process.env.NEXT_PUBLIC_TIKTOK_PIXEL_ID;
const TIKTOK_ACCESS_TOKEN = process.env.TIKTOK_EVENTS_API_ACCESS_TOKEN;

const SITE_URL = "https://shirtfaced.wtf";

function sha256(value: string) {
  return createHash("sha256").update(value.trim().toLowerCase()).digest("hex");
}

/**
 * Pulls the browser-side signals Meta/TikTok use to match a server event
 * back to the visitor who generated it (client IP, user agent, and each
 * platform's own first-party cookie). Called from create-payment-intent at
 * checkout time — the only point in this flow where the customer's own
 * request is still in hand — and threaded through as Stripe PaymentIntent
 * metadata so the webhook can read it back once payment settles.
 */
export function extractRequestMatchData(request: Request) {
  const cookieHeader = request.headers.get("cookie") ?? "";
  const cookie = (name: string) =>
    cookieHeader.match(new RegExp(`(?:^|; )${name}=([^;]+)`))?.[1] ?? null;

  return {
    clientIp: request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? null,
    userAgent: request.headers.get("user-agent")?.slice(0, 500) ?? null,
    fbp: cookie("_fbp"),
    fbc: cookie("_fbc"),
    ttp: cookie("_ttp"),
  };
}

export type ServerPurchaseContent = {
  contentId: string;
  quantity: number;
};

export type ServerPurchase = {
  transactionId: string;
  value: number;
  currency: "AUD";
  email: string;
  /** Captured at checkout time (see create-payment-intent/route.ts) — the
   * webhook call itself comes from Stripe's servers, not the customer's
   * browser, so none of this is available at the point the event fires. */
  clientIp: string | null;
  userAgent: string | null;
  fbp: string | null;
  fbc: string | null;
  ttp: string | null;
  /** Per-product line items, fetched separately from admin by the webhook
   * (the PaymentIntent itself doesn't carry them) — both platforms' own
   * event-quality checks flag a Purchase with no content_id, since it's what
   * catalog-linked ad optimization needs to map a sale back to products. */
  contents: ServerPurchaseContent[];
};

export async function sendServerSidePurchase(purchase: ServerPurchase) {
  await Promise.all([sendMetaCapiPurchase(purchase), sendTikTokEventsApiPurchase(purchase)]);
}

async function sendMetaCapiPurchase(purchase: ServerPurchase) {
  if (!META_PIXEL_ID || !META_ACCESS_TOKEN) return;

  const body = {
    data: [
      {
        event_name: "Purchase",
        event_time: Math.floor(Date.now() / 1000),
        event_id: purchase.transactionId,
        event_source_url: `${SITE_URL}/checkout/success`,
        action_source: "website",
        user_data: {
          em: [sha256(purchase.email)],
          ...(purchase.clientIp && { client_ip_address: purchase.clientIp }),
          ...(purchase.userAgent && { client_user_agent: purchase.userAgent }),
          ...(purchase.fbp && { fbp: purchase.fbp }),
          ...(purchase.fbc && { fbc: purchase.fbc }),
        },
        custom_data: {
          value: purchase.value,
          currency: purchase.currency,
          contents: purchase.contents.map((c) => ({ id: c.contentId, quantity: c.quantity })),
          content_type: "product",
        },
      },
    ],
  };

  const res = await fetch(
    `https://graph.facebook.com/v21.0/${META_PIXEL_ID}/events?access_token=${META_ACCESS_TOKEN}`,
    { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) },
  );
  if (!res.ok) {
    console.error(`meta CAPI: ${res.status} ${await res.text().catch(() => "")}`);
  }
}

async function sendTikTokEventsApiPurchase(purchase: ServerPurchase) {
  if (!TIKTOK_PIXEL_ID || !TIKTOK_ACCESS_TOKEN) return;

  const body = {
    event_source: "web",
    event_source_id: TIKTOK_PIXEL_ID,
    data: [
      {
        event: "CompletePayment",
        event_time: Math.floor(Date.now() / 1000),
        event_id: purchase.transactionId,
        user: {
          email: sha256(purchase.email),
          ...(purchase.clientIp && { ip: purchase.clientIp }),
          ...(purchase.userAgent && { user_agent: purchase.userAgent }),
          ...(purchase.ttp && { ttp: purchase.ttp }),
        },
        page: { url: `${SITE_URL}/checkout/success` },
        properties: {
          currency: purchase.currency,
          value: purchase.value,
          contents: purchase.contents.map((c) => ({
            content_id: c.contentId,
            content_type: "product",
            quantity: c.quantity,
          })),
        },
      },
    ],
  };

  const res = await fetch("https://business-api.tiktok.com/open_api/v1.3/event/track/", {
    method: "POST",
    headers: { "content-type": "application/json", "Access-Token": TIKTOK_ACCESS_TOKEN },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    console.error(`tiktok events API: ${res.status} ${await res.text().catch(() => "")}`);
  }
}

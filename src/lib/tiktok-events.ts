import { createHash } from "node:crypto";

const TIKTOK_EVENTS_API_URL = "https://business-api.tiktok.com/open_api/v1.3/event/track/";

function hashForTikTok(value: string): string {
  return createHash("sha256").update(value.trim().toLowerCase()).digest("hex");
}

/**
 * Server half of Purchase tracking, called from the Stripe webhook once a
 * payment_intent actually succeeds — same "server is the source of truth"
 * reasoning as the order-paid PATCH right above its call site. Shares
 * event_id (the order id) with the client pixel's CompletePayment call in
 * checkout/success, so TikTok dedupes the two into one conversion.
 *
 * Best-effort: a failure here is a missed ad-attribution signal, not a
 * broken order, so callers should catch and log rather than let it fail
 * the webhook.
 */
export async function sendTikTokPurchaseEvent({
  orderId,
  valueCents,
  currency,
  email,
}: {
  orderId: string;
  valueCents: number;
  currency: string;
  email: string | null;
}): Promise<void> {
  const pixelCode = process.env.NEXT_PUBLIC_TIKTOK_PIXEL_ID;
  const accessToken = process.env.TIKTOK_EVENTS_API_ACCESS_TOKEN;
  if (!pixelCode || !accessToken) return;

  const response = await fetch(TIKTOK_EVENTS_API_URL, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "Access-Token": accessToken,
    },
    body: JSON.stringify({
      event_source: "web",
      event_source_id: pixelCode,
      data: [
        {
          event: "CompletePayment",
          event_time: Math.floor(Date.now() / 1000),
          event_id: orderId,
          user: email ? { email: hashForTikTok(email) } : {},
          properties: {
            currency: currency.toUpperCase(),
            value: valueCents / 100,
          },
        },
      ],
    }),
  });

  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new Error(`TikTok Events API responded ${response.status}: ${body}`);
  }
}

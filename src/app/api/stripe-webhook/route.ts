import { NextResponse } from "next/server";
import Stripe from "stripe";
import { sendTikTokPurchaseEvent } from "@/lib/tiktok-events";

/**
 * Stripe calls this directly (server to server), never the browser — this is
 * the only thing that should ever mark an order "paid". The browser side of
 * checkout confirming a payment (see checkout/PaymentStep.tsx) is not proof
 * a charge actually settled: the tab can close, the network can drop, or the
 * card can need a bank's own follow-up (3DS) that finishes after redirect.
 * Stripe's webhook fires once the money has actually moved, independent of
 * whether the customer's browser is still there to hear about it.
 */
export async function POST(request: Request) {
  const stripeSecretKey = process.env.STRIPE_SECRET_KEY;
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;
  const adminApiUrl = process.env.ADMIN_API_URL;
  const adminApiKey = process.env.ADMIN_INTERNAL_API_KEY;

  if (!stripeSecretKey || !webhookSecret || !adminApiUrl || !adminApiKey) {
    return NextResponse.json({ error: "Webhook isn't configured." }, { status: 503 });
  }

  const signature = request.headers.get("stripe-signature");
  if (!signature) {
    return NextResponse.json({ error: "Missing stripe-signature header." }, { status: 400 });
  }

  // Signature verification needs the exact bytes Stripe sent, not a
  // re-serialised parse of them — text(), not json().
  const rawBody = await request.text();
  const stripe = new Stripe(stripeSecretKey);

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(rawBody, signature, webhookSecret);
  } catch (error) {
    return NextResponse.json(
      { error: `Signature verification failed: ${(error as Error).message}` },
      { status: 400 },
    );
  }

  if (event.type === "payment_intent.succeeded") {
    const paymentIntent = event.data.object as Stripe.PaymentIntent;
    const orderId = paymentIntent.metadata.orderId;
    if (orderId) {
      const patchResponse = await fetch(`${adminApiUrl}/api/internal/orders/${orderId}`, {
        method: "PATCH",
        headers: { "content-type": "application/json", "x-internal-api-key": adminApiKey },
        body: JSON.stringify({ status: "paid" }),
      });
      // A non-2xx here means a paid order is stuck showing "pending" in
      // admin until someone notices — loud in the logs on purpose, and a
      // 500 back to Stripe so it retries the webhook on its own schedule
      // rather than this event being silently dropped.
      if (!patchResponse.ok) {
        console.error(
          `stripe-webhook: failed to mark order ${orderId} paid (${patchResponse.status})`,
        );
        return NextResponse.json({ error: "Could not update the order." }, { status: 500 });
      }

      // Ad-attribution signal, not order state — logged on failure, never
      // allowed to fail the webhook itself. Line items are a second
      // best-effort fetch: TikTok's own event-quality check flags a Purchase
      // with no content_id, which needs per-product ids the PaymentIntent
      // itself doesn't carry — a fetch failure here just means the event
      // goes out without contents, not that it doesn't go out at all.
      const itemsResponse = await fetch(`${adminApiUrl}/api/internal/orders/${orderId}`, {
        headers: { "x-internal-api-key": adminApiKey },
      }).catch(() => null);
      const itemsBody = itemsResponse?.ok
        ? ((await itemsResponse.json().catch(() => null)) as {
            items: { productId: string | null; productName: string; quantity: number }[];
          } | null)
        : null;

      await sendTikTokPurchaseEvent({
        orderId,
        valueCents: paymentIntent.amount,
        currency: paymentIntent.currency,
        email: paymentIntent.receipt_email,
        contents: (itemsBody?.items ?? []).map((item) => ({
          contentId: item.productId ?? item.productName,
          quantity: item.quantity,
        })),
      }).catch((error) => {
        console.error(`stripe-webhook: TikTok purchase event failed for order ${orderId}`, error);
      });
    }
  }

  return NextResponse.json({ received: true });
}

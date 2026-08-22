import { NextResponse } from "next/server";
import Stripe from "stripe";

/**
 * Stripe calls this server-to-server — the only thing that should ever mark
 * an order "paid". Marking an order paid in curbstamps-admin is also what
 * triggers the POD fulfilment call (see admin's markOrderPaid /
 * lib/pod/index.ts) — this webhook firing is the moment a real order enters
 * production, not the browser redirecting back successfully.
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

  const rawBody = await request.text();
  const stripe = new Stripe(stripeSecretKey);

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(rawBody, signature, webhookSecret);
  } catch (error) {
    return NextResponse.json({ error: `Signature verification failed: ${(error as Error).message}` }, { status: 400 });
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
      if (!patchResponse.ok) {
        console.error(`stripe-webhook: failed to mark order ${orderId} paid (${patchResponse.status})`);
        return NextResponse.json({ error: "Could not update the order." }, { status: 500 });
      }
    }
  }

  return NextResponse.json({ received: true });
}

import { NextResponse } from "next/server";
import Stripe from "stripe";
import { priceCart, CheckoutPricingError, type CartLineInput } from "@/lib/checkout-pricing";

/**
 * Called from the checkout page once the customer reaches the review step.
 * Recomputes the total server-side (never trusts what the browser sent),
 * creates a pending order in admin's database via its internal API (this app
 * has no direct DB access — SHOP_DATABASE_URL here is a read-only role, used
 * only at build time by scripts/sync-products.mjs), then creates a Stripe
 * PaymentIntent for that exact amount and hands its client secret back so
 * the browser can collect card details in Stripe's own embedded element.
 */
type RequestBody = {
  lines: CartLineInput[];
  shippingMethod: string;
  contact: { email: string; name: string };
  address: { line1: string; suburb: string; state: string; postcode: string };
};

function isRequestBody(value: unknown): value is RequestBody {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    Array.isArray(v.lines) &&
    typeof v.shippingMethod === "string" &&
    !!v.contact &&
    typeof (v.contact as Record<string, unknown>).email === "string" &&
    typeof (v.contact as Record<string, unknown>).name === "string" &&
    !!v.address &&
    typeof (v.address as Record<string, unknown>).line1 === "string" &&
    typeof (v.address as Record<string, unknown>).suburb === "string" &&
    typeof (v.address as Record<string, unknown>).state === "string" &&
    typeof (v.address as Record<string, unknown>).postcode === "string"
  );
}

export async function POST(request: Request) {
  const stripeSecretKey = process.env.STRIPE_SECRET_KEY;
  const adminApiUrl = process.env.ADMIN_API_URL;
  const adminApiKey = process.env.ADMIN_INTERNAL_API_KEY;

  if (!stripeSecretKey) {
    return NextResponse.json(
      { error: "Payments aren't connected yet.", notConfigured: true },
      { status: 503 },
    );
  }
  if (!adminApiUrl || !adminApiKey) {
    return NextResponse.json(
      { error: "The order backend isn't connected yet.", notConfigured: true },
      { status: 503 },
    );
  }

  const json = await request.json().catch(() => null);
  if (!isRequestBody(json)) {
    return NextResponse.json({ error: "Invalid request." }, { status: 400 });
  }

  let priced;
  try {
    priced = priceCart(json.lines, json.shippingMethod);
  } catch (error) {
    if (error instanceof CheckoutPricingError) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }
    throw error;
  }

  const shippingAddress = `${json.address.line1}, ${json.address.suburb} ${json.address.state} ${json.address.postcode}`;

  const orderResponse = await fetch(`${adminApiUrl}/api/internal/orders`, {
    method: "POST",
    headers: { "content-type": "application/json", "x-internal-api-key": adminApiKey },
    body: JSON.stringify({
      customer: { email: json.contact.email, name: json.contact.name },
      shippingCents: priced.shippingCents,
      shippingAddress,
      items: priced.lines.map((line) => ({
        slug: line.slug,
        productName: line.name,
        colourName: line.colour,
        size: line.size,
        quantity: line.quantity,
        unitPriceCents: line.unitPriceCents,
      })),
    }),
  });

  if (!orderResponse.ok) {
    return NextResponse.json(
      { error: "Couldn't start your order. Try again in a moment." },
      { status: 502 },
    );
  }
  const { orderId } = (await orderResponse.json()) as { orderId: string };

  const stripe = new Stripe(stripeSecretKey);
  const paymentIntent = await stripe.paymentIntents.create({
    amount: priced.totalCents,
    currency: "aud",
    receipt_email: json.contact.email,
    metadata: { orderId },
  });

  // Best-effort — the order already exists and the payment already has an
  // id even if this particular call fails; staff can still find it by
  // searching Stripe for the amount/email. Not worth failing checkout over.
  await fetch(`${adminApiUrl}/api/internal/orders/${orderId}`, {
    method: "PATCH",
    headers: { "content-type": "application/json", "x-internal-api-key": adminApiKey },
    body: JSON.stringify({ stripePaymentIntentId: paymentIntent.id }),
  }).catch(() => {});

  return NextResponse.json({ clientSecret: paymentIntent.client_secret, orderId });
}

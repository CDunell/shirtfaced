import { NextResponse } from "next/server";
import { priceCart, CheckoutPricingError, type CartLineInput } from "@/lib/checkout-pricing";

/**
 * Preview-only: tells the checkout page what a code is worth before the
 * customer pays. Never mutates anything — real redemption (and the usage
 * limit check that has to be race-free) happens once, atomically, when the
 * order is actually created — see admin's redeemDiscountByCode. A code that
 * previews fine here can still be rejected at that point (exhausted or
 * expired in between); the checkout page handles that as a real error, not
 * a bug.
 */
type RequestBody = { code: string; lines: CartLineInput[] };

function isRequestBody(value: unknown): value is RequestBody {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return typeof v.code === "string" && Array.isArray(v.lines);
}

export async function POST(request: Request) {
  const adminApiUrl = process.env.ADMIN_API_URL;
  const adminApiKey = process.env.ADMIN_INTERNAL_API_KEY;
  if (!adminApiUrl || !adminApiKey) {
    return NextResponse.json({ error: "Discount codes aren't connected yet." }, { status: 503 });
  }

  const json = await request.json().catch(() => null);
  if (!isRequestBody(json)) {
    return NextResponse.json({ error: "Invalid request." }, { status: 400 });
  }

  let subtotalCents: number;
  try {
    // Shipping method doesn't affect subtotal — "standard" is just a valid
    // key to satisfy priceCart, not a claim about what the customer picked.
    subtotalCents = priceCart(json.lines, "standard").subtotalCents;
  } catch (error) {
    if (error instanceof CheckoutPricingError) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }
    throw error;
  }

  const lookupResponse = await fetch(`${adminApiUrl}/api/internal/discounts/lookup`, {
    method: "POST",
    headers: { "content-type": "application/json", "x-internal-api-key": adminApiKey },
    body: JSON.stringify({ code: json.code }),
  });

  if (!lookupResponse.ok) {
    const body = await lookupResponse.json().catch(() => ({}));
    return NextResponse.json({ error: body.error ?? "That code isn't valid." }, { status: 404 });
  }

  const { discount } = (await lookupResponse.json()) as {
    discount: { code: string; type: "percent" | "fixed"; value: number };
  };

  const discountCents =
    discount.type === "percent"
      ? Math.round((subtotalCents * discount.value) / 100)
      : Math.min(discount.value, subtotalCents);

  return NextResponse.json({ code: discount.code, discountCents });
}

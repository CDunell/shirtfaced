import { NextResponse } from "next/server";
import { getShippingQuote } from "@/lib/shipping-quote";
import type { CartLineInput } from "@/lib/checkout-pricing";

/** Called from checkout step 2 once the address is complete, so the
 * shipping method list shows a real price instead of a guess. */
export async function POST(request: Request) {
  const json = await request.json().catch(() => null);
  if (
    !json ||
    !Array.isArray(json.lines) ||
    json.lines.length === 0 ||
    !json.address ||
    typeof json.address.line1 !== "string"
  ) {
    return NextResponse.json({ error: "Invalid request." }, { status: 400 });
  }

  const quote = await getShippingQuote(json.lines as CartLineInput[], json.address);
  return NextResponse.json(quote);
}

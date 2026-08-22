import { NextResponse } from "next/server";
import { z } from "zod";
import { verifyInternalRequest } from "@/lib/internal-auth";
import { getPodProvider, PodError } from "@/lib/pod";

/**
 * Called by curbstamps-site's checkout before payment, to price shipping
 * for the real cart and address instead of a flat rate — see
 * PodProvider.getShippingQuote's own comment for why a flat rate doesn't
 * work for a worldwide launch. The storefront falls back to a static
 * estimate if this call fails or isn't configured (see checkout-pricing.ts
 * there) rather than blocking checkout entirely.
 */
const bodySchema = z.object({
  address: z.object({
    name: z.string().min(1),
    line1: z.string().min(1),
    suburb: z.string().min(1),
    state: z.string(),
    postcode: z.string().min(1),
    country: z.string().min(2),
  }),
  items: z
    .array(
      z.object({
        slug: z.string().min(1),
        productName: z.string().min(1),
        colourName: z.string().nullable(),
        size: z.string().nullable(),
        quantity: z.number().int().positive(),
      }),
    )
    .min(1),
});

export async function POST(request: Request) {
  if (!verifyInternalRequest(request)) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const json = await request.json().catch(() => null);
  const parsed = bodySchema.safeParse(json);
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.issues[0]?.message ?? "Invalid request body." }, { status: 400 });
  }

  try {
    const quote = await getPodProvider().getShippingQuote(parsed.data);
    return NextResponse.json(quote);
  } catch (error) {
    const message = error instanceof PodError ? error.message : "Unknown shipping quote error.";
    console.error(`shipping-quote: ${message}`);
    return NextResponse.json({ error: message }, { status: 502 });
  }
}

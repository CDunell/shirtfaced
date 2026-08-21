import { NextResponse } from "next/server";
import { z } from "zod";
import { verifyInternalRequest } from "@/lib/internal-auth";
import { findOrderForCustomer, orderReference } from "@/db/store-queries";

/**
 * Called by the storefront's account/order-tracking page — see
 * src/app/api/order-status/route.ts. Requires the exact email on the order,
 * not just its reference (see findOrderForCustomer), and only ever returns
 * the subset of an order a customer should see — never notes, the Stripe
 * PaymentIntent id, or the full customer record.
 */
const bodySchema = z.object({
  reference: z.string().min(1),
  email: z.string().email(),
});

export async function POST(request: Request) {
  if (!verifyInternalRequest(request)) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const json = await request.json().catch(() => null);
  const parsed = bodySchema.safeParse(json);
  if (!parsed.success) {
    return NextResponse.json({ error: "Enter an order number and email." }, { status: 400 });
  }

  const order = await findOrderForCustomer(parsed.data.reference, parsed.data.email);
  if (!order) {
    return NextResponse.json(
      { error: "No order found for that number and email." },
      { status: 404 },
    );
  }

  return NextResponse.json({
    order: {
      reference: orderReference(order.orderSeq),
      status: order.status,
      createdAt: order.createdAt,
      trackingNumber: order.trackingNumber,
      carrier: order.carrier,
      subtotalCents: order.subtotalCents,
      discountCents: order.discountCents,
      shippingCents: order.shippingCents,
      totalCents: order.totalCents,
      items: order.items.map((item) => ({
        productName: item.productName,
        colourName: item.colourName,
        size: item.size,
        quantity: item.quantity,
        unitPriceCents: item.unitPriceCents,
      })),
    },
  });
}

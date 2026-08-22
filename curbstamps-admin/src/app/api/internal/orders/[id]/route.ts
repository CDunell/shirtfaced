import { NextResponse } from "next/server";
import { z } from "zod";
import { verifyInternalRequest } from "@/lib/internal-auth";
import { ORDER_STATUSES } from "@/db/schema";
import { getOrderItemsById, markOrderPaid, setOrderPaymentIntent, updateOrderStatus } from "@/db/store-queries";

export async function GET(request: Request, { params }: { params: Promise<{ id: string }> }) {
  if (!verifyInternalRequest(request)) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const { id } = await params;
  const items = await getOrderItemsById(id);
  if (!items) {
    return NextResponse.json({ error: "Order not found." }, { status: 404 });
  }

  return NextResponse.json({
    items: items.map((item) => ({ productId: item.productId, productName: item.productName, quantity: item.quantity })),
  });
}

/**
 * Called by curbstamps-site twice per real order: once right after creating
 * the Stripe PaymentIntent (to record its id for support lookups), and once
 * from its Stripe webhook, to flip status to "paid" once Stripe confirms
 * the charge — the only caller that should ever send status: "paid".
 */
const bodySchema = z
  .object({
    status: z.enum(ORDER_STATUSES).optional(),
    stripePaymentIntentId: z.string().min(1).optional(),
  })
  .refine((v) => v.status !== undefined || v.stripePaymentIntentId !== undefined, {
    message: "Provide at least one of status or stripePaymentIntentId.",
  });

export async function PATCH(request: Request, { params }: { params: Promise<{ id: string }> }) {
  if (!verifyInternalRequest(request)) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const { id } = await params;
  const json = await request.json().catch(() => null);
  const parsed = bodySchema.safeParse(json);
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.issues[0]?.message ?? "Invalid request body." }, { status: 400 });
  }

  if (parsed.data.stripePaymentIntentId) {
    await setOrderPaymentIntent(id, parsed.data.stripePaymentIntentId);
  }
  if (parsed.data.status === "paid") {
    await markOrderPaid(id);
  } else if (parsed.data.status) {
    await updateOrderStatus(id, parsed.data.status);
  }

  return NextResponse.json({ ok: true });
}

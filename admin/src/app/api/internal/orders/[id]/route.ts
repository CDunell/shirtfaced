import { NextResponse } from "next/server";
import { z } from "zod";
import { verifyInternalRequest } from "@/lib/internal-auth";
import { ORDER_STATUSES } from "@/db/schema";
import { setOrderPaymentIntent, updateOrderStatus } from "@/db/store-queries";

/**
 * Called by the storefront twice per real order: once right after creating
 * the Stripe PaymentIntent, to record its id against the order for support
 * lookups, and once from the Stripe webhook, to flip status to "paid" once
 * Stripe actually confirms the charge. The webhook is the only caller that
 * should ever send status: "paid" — see its own comment for why that
 * confirmation can't come from the client redirecting back successfully.
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
    return NextResponse.json(
      { error: parsed.error.issues[0]?.message ?? "Invalid request body." },
      { status: 400 },
    );
  }

  if (parsed.data.stripePaymentIntentId) {
    await setOrderPaymentIntent(id, parsed.data.stripePaymentIntentId);
  }
  if (parsed.data.status) {
    await updateOrderStatus(id, parsed.data.status);
  }

  return NextResponse.json({ ok: true });
}

import { NextResponse } from "next/server";
import { z } from "zod";
import { timingSafeEqual } from "node:crypto";
import { updateOrderFromPodWebhook } from "@/db/store-queries";

/**
 * Inbound fulfilment status updates from the POD provider. The mock adapter
 * never calls this — it has no webhook of its own — but a real vendor
 * (Printful, Printify) POSTs here on production/shipped events once
 * configured in their dashboard. Shape is intentionally generic (status +
 * optional tracking fields) rather than one vendor's exact payload, so
 * swapping providers later means changing how this route maps their payload
 * into this shape, not the order-update logic itself.
 *
 * Authenticated with a shared secret in a header, same pattern as
 * /api/internal — POD_WEBHOOK_SECRET must match whatever the vendor's
 * webhook config sends (most vendors let you set a custom header or a
 * signing secret; check the real provider's docs when wiring this up for
 * real and adjust the header name/verification below to match).
 */
function verifyPodWebhook(request: Request): boolean {
  const expected = process.env.POD_WEBHOOK_SECRET;
  const provided = request.headers.get("x-pod-webhook-secret");
  if (!expected || !provided) return false;
  const a = Buffer.from(provided);
  const b = Buffer.from(expected);
  if (a.length !== b.length) return false;
  return timingSafeEqual(a, b);
}

const bodySchema = z.object({
  podOrderId: z.string().min(1),
  status: z.string().min(1),
  trackingNumber: z.string().optional(),
  trackingUrl: z.string().optional(),
  carrier: z.string().optional(),
});

export async function POST(request: Request) {
  if (!verifyPodWebhook(request)) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const json = await request.json().catch(() => null);
  const parsed = bodySchema.safeParse(json);
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.issues[0]?.message ?? "Invalid payload." }, { status: 400 });
  }

  const orderId = await updateOrderFromPodWebhook(parsed.data.podOrderId, parsed.data);
  if (!orderId) {
    // 200, not 404 — an update for an order this app doesn't recognise
    // (wrong environment, stale webhook config) shouldn't make the vendor
    // retry forever.
    console.warn(`pod webhook: no order found for podOrderId ${parsed.data.podOrderId}`);
  }

  return NextResponse.json({ received: true });
}

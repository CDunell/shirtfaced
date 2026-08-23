import { NextResponse } from "next/server";
import { z } from "zod";
import { createHmac, timingSafeEqual } from "node:crypto";
import { updateOrderFromPodWebhook } from "@/db/store-queries";
import { getPodProvider, PodError } from "@/lib/pod";

/**
 * Inbound fulfilment status updates from Printify — registered subscriptions
 * (order:updated, order:sent-to-production, order:shipment:created,
 * order:shipment:delivered) all POST here. Payload shape confirmed against
 * a real event via Printify's own simulate endpoint
 * (POST /webhooks/{id}/simulate), not guessed from docs:
 *
 *   { id, type: "order:updated", created_at, resource: { id, type: "order", data } }
 *
 * `resource.data` is empty even on a real simulated event — Printify's
 * pattern here is notify-then-fetch, not push-full-state — so this doesn't
 * try to read status/tracking out of the payload itself. It just takes
 * resource.id as the signal "this order changed" and re-fetches the
 * authoritative state via the same getOrderStatus() the adapter already
 * uses (and that's already been verified against the real API), then
 * applies it the same way a manual status check would.
 *
 * Verified with HMAC-SHA256 over the raw body, header `x-pfy-signature:
 * sha256={hex}`, key = the same secret set when creating the webhook
 * subscription (POD_WEBHOOK_SECRET) — see "Securing your webhooks" at
 * developers.printify.com.
 */
function verifySignature(rawBody: string, header: string | null): boolean {
  const secret = process.env.POD_WEBHOOK_SECRET;
  if (!secret || !header) return false;
  const expectedHex = createHmac("sha256", secret).update(rawBody).digest("hex");
  const provided = header.startsWith("sha256=") ? header.slice("sha256=".length) : header;
  const a = Buffer.from(provided);
  const b = Buffer.from(expectedHex);
  if (a.length !== b.length) return false;
  return timingSafeEqual(a, b);
}

const bodySchema = z.object({
  type: z.string(),
  resource: z
    .object({
      id: z.string(),
      type: z.string(),
    })
    .optional(),
});

export async function POST(request: Request) {
  const rawBody = await request.text();

  if (!verifySignature(rawBody, request.headers.get("x-pfy-signature"))) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const json = JSON.parse(rawBody || "null");
  const parsed = bodySchema.safeParse(json);
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.issues[0]?.message ?? "Invalid payload." }, { status: 400 });
  }

  const { type, resource } = parsed.data;
  if (!resource || resource.type !== "order") {
    // Personalization events and anything else we haven't subscribed to on
    // purpose — 200 so Printify doesn't retry, nothing to do here.
    return NextResponse.json({ received: true, ignored: true });
  }

  try {
    const status = await getPodProvider().getOrderStatus(resource.id);
    const orderId = await updateOrderFromPodWebhook(resource.id, status);
    if (!orderId) {
      // 200, not 404 — an update for an order this app doesn't recognise
      // (wrong environment, stale webhook config) shouldn't make Printify
      // retry forever.
      console.warn(`pod webhook: no order found for podOrderId ${resource.id} (event ${type})`);
    }
  } catch (error) {
    // The webhook only told us "something changed" — if the follow-up
    // status fetch fails, log and still 200 (Printify's own state hasn't
    // changed because of this; a later event or a manual check will catch
    // it up). Don't turn a transient fetch failure into a retry storm.
    console.error(`pod webhook: status fetch failed for ${resource.id}`, error instanceof PodError ? error.message : error);
  }

  return NextResponse.json({ received: true });
}

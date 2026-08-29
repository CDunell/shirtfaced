import { eq, desc, and } from "drizzle-orm";
import { db } from "./client";
import { customers, newsletterSubscribers, orders, orderItems, products, type OrderStatus } from "./schema";
import { getPodProvider, PodError } from "../lib/pod";

export async function findProductIdBySlug(slug: string): Promise<string | null> {
  const row = await db.query.products.findFirst({ where: eq(products.slug, slug), columns: { id: true } });
  return row?.id ?? null;
}

/** Find-or-create by email, for checkout. */
export async function upsertCustomerByEmail(email: string, name: string): Promise<string> {
  const [{ id }] = await db
    .insert(customers)
    .values({ email, name })
    .onConflictDoUpdate({ target: customers.email, set: { name } })
    .returning({ id: customers.id });
  return id;
}

/** Idempotent: signing up twice is a no-op, not an error. */
export async function addNewsletterSubscriber(email: string, source: string): Promise<void> {
  await db
    .insert(newsletterSubscribers)
    .values({ email: email.trim().toLowerCase(), source })
    .onConflictDoNothing({ target: newsletterSubscribers.email });
}

/* ---------------------------------------------------------------------------
   Orders. Reached two ways: curbstamps-site's checkout, through
   app/api/internal/orders (the storefront has no direct database access —
   see that route's own comment), and staff directly in this admin's UI.
--------------------------------------------------------------------------- */

export function listOrders() {
  return db.query.orders.findMany({
    with: { customer: true, items: true },
    orderBy: [desc(orders.createdAt)],
  });
}

export function getOrderById(id: string) {
  return db.query.orders.findFirst({
    where: eq(orders.id, id),
    with: { customer: true, items: true },
  });
}

export async function getOrderItemsById(id: string) {
  const order = await db.query.orders.findFirst({ where: eq(orders.id, id), with: { items: true } });
  return order?.items ?? null;
}

export type OrderItemInput = {
  productId: string | null;
  productName: string;
  colourName: string | null;
  size: string | null;
  quantity: number;
  unitPriceCents: number;
};

export type OrderInput = {
  customerId: string;
  status: OrderStatus;
  shippingCents: number;
  shippingAddress: string;
  notes: string;
  items: OrderItemInput[];
};

export async function createOrder(data: OrderInput) {
  const subtotalCents = data.items.reduce((sum, item) => sum + item.quantity * item.unitPriceCents, 0);
  const totalCents = subtotalCents + data.shippingCents;

  return db.transaction(async (tx) => {
    const [{ id }] = await tx
      .insert(orders)
      .values({
        customerId: data.customerId,
        status: data.status,
        subtotalCents,
        shippingCents: data.shippingCents,
        totalCents,
        shippingAddress: data.shippingAddress,
        notes: data.notes,
      })
      .returning({ id: orders.id });

    if (data.items.length > 0) {
      await tx.insert(orderItems).values(data.items.map((item) => ({ ...item, orderId: id })));
    }

    return id;
  });
}

export async function updateOrderStatus(id: string, status: OrderStatus) {
  await db.update(orders).set({ status, updatedAt: new Date() }).where(eq(orders.id, id));
}

export async function setOrderPaymentIntent(id: string, stripePaymentIntentId: string) {
  await db.update(orders).set({ stripePaymentIntentId, updatedAt: new Date() }).where(eq(orders.id, id));
}

/**
 * The only path that should move an order into "paid" — called by
 * curbstamps-site's Stripe webhook, and by staff manually in this admin.
 * Guarded on the order not already being paid: Stripe retries webhooks, and
 * without this a retried event would submit the same order to the POD
 * provider twice.
 *
 * Submitting to POD happens in the same call, not a separate queue/worker —
 * there's no order volume yet to need one (see docs/curbstamps/
 * CURB_STAMPS_SPEC.md §4 for when that stops being true). A POD failure
 * doesn't roll back the "paid" status — the customer has genuinely paid —
 * it's recorded on the order's notes so staff see it in the order list and
 * can retry or submit by hand.
 */
export async function markOrderPaid(id: string): Promise<void> {
  const order = await db.transaction(async (tx) => {
    const found = await tx.query.orders.findFirst({
      where: eq(orders.id, id),
      with: { items: { with: { product: true } }, customer: true },
    });
    if (!found || found.status === "paid") return null;

    await tx.update(orders).set({ status: "paid", updatedAt: new Date() }).where(eq(orders.id, id));
    return found;
  });

  if (!order) return;

  try {
    const provider = getPodProvider();
    const [line1, rest] = (order.shippingAddress ?? "").split(", ");
    const [suburb, stateAndPostcode] = (rest ?? "").split(/\s+(?=\S+$)/);
    const result = await provider.createOrder({
      orderRef: order.id,
      address: {
        name: order.customer?.name ?? "",
        line1: line1 ?? "",
        suburb: suburb ?? "",
        state: (stateAndPostcode ?? "").split(" ")[0] ?? "",
        postcode: (stateAndPostcode ?? "").split(" ")[1] ?? "",
        country: "AU",
      },
      items: order.items.map((item) => ({
        // The real product slug (e.g. "blip-tee"), via the product this
        // order item snapshot points at — falls back to the product-name
        // snapshot only if that product's since been deleted, in which case
        // no POD provider can resolve it either and this fails the same way
        // an unmapped slug already does (caught below, recorded on notes).
        slug: item.product?.slug ?? item.productName,
        productName: item.productName,
        colourName: item.colourName,
        size: item.size,
        quantity: item.quantity,
      })),
    });

    await db
      .update(orders)
      .set({
        podProvider: provider.name,
        podOrderId: result.podOrderId,
        podStatus: result.status,
        updatedAt: new Date(),
      })
      .where(eq(orders.id, id));
  } catch (error) {
    const message = error instanceof PodError ? error.message : "Unknown POD submission error.";
    console.error(`markOrderPaid: POD submission failed for order ${id}: ${message}`);
    await db
      .update(orders)
      .set({ notes: `POD submission failed: ${message}`, updatedAt: new Date() })
      .where(eq(orders.id, id));
  }
}

export async function cancelOrder(id: string) {
  await db.update(orders).set({ status: "cancelled", updatedAt: new Date() }).where(eq(orders.id, id));
}

/** Called from app/api/pod/webhook once a real provider sends a status
 * update — matches on podOrderId, not this app's own order id. */
export async function updateOrderFromPodWebhook(
  podOrderId: string,
  data: { status: string; trackingNumber?: string; trackingUrl?: string; carrier?: string },
) {
  const order = await db.query.orders.findFirst({ where: eq(orders.podOrderId, podOrderId) });
  if (!order) return null;

  const nextStatus =
    data.status === "fulfilled" || data.status === "shipped"
      ? "shipped"
      : data.status === "in_production" || data.status === "pending"
        ? "in_production"
        : order.status;

  await db
    .update(orders)
    .set({
      status: nextStatus,
      podStatus: data.status,
      trackingNumber: data.trackingNumber ?? order.trackingNumber,
      trackingUrl: data.trackingUrl ?? order.trackingUrl,
      carrier: data.carrier ?? order.carrier,
      updatedAt: new Date(),
    })
    .where(and(eq(orders.id, order.id)));

  return order.id;
}

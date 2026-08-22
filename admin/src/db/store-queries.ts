import { and, eq, isNull, lt, sql } from "drizzle-orm";
import { db } from "./client";
import {
  colourStock,
  customers,
  discounts,
  orderItems,
  orders,
  products,
  productColours,
  type DiscountType,
  type OrderStatus,
  type Size,
} from "./schema";
import { getStripe } from "../lib/stripe";
import {
  sendAbandonedCartEmail,
  sendOrderConfirmationEmail,
  sendShippingConfirmationEmail,
} from "../lib/email";

/* ---------------------------------------------------------------------------
   Customers
--------------------------------------------------------------------------- */

export function listCustomers() {
  return db.query.customers.findMany({
    orderBy: (c, { desc: d }) => d(c.createdAt),
  });
}

export function getCustomer(id: string) {
  return db.query.customers.findFirst({
    where: eq(customers.id, id),
    with: { orders: { orderBy: (o, { desc: d }) => d(o.createdAt) } },
  });
}

export interface CustomerInput {
  email: string;
  name: string;
  phone: string | null;
  addressLine1: string | null;
  addressLine2: string | null;
  suburb: string | null;
  state: string | null;
  postcode: string | null;
  country: string;
  notes: string | null;
}

export async function createCustomer(data: CustomerInput) {
  const [{ id }] = await db.insert(customers).values(data).returning({ id: customers.id });
  return id;
}

export async function updateCustomer(id: string, data: CustomerInput) {
  await db
    .update(customers)
    .set({ ...data, updatedAt: new Date() })
    .where(eq(customers.id, id));
}

export async function deleteCustomer(id: string) {
  await db.delete(customers).where(eq(customers.id, id));
}

/** Resolves a storefront cart line's slug to its current productId, for the
 * checkout order-creation path — null if the product's been deleted since it
 * was added to a cart (order still goes through with just the name snapshot,
 * same graceful degradation the schema already documents for productId). */
export async function findProductIdBySlug(slug: string): Promise<string | null> {
  const row = await db.query.products.findFirst({
    where: eq(products.slug, slug),
    columns: { id: true },
  });
  return row?.id ?? null;
}

/** Find-or-create by email, for checkout — a customer's email is the only
 * thing guaranteed present at that point, and it's already unique. Updates
 * the name on an existing row rather than ignoring it, since a repeat buyer
 * typing their name slightly differently shouldn't fork two records. */
export async function upsertCustomerByEmail(email: string, name: string): Promise<string> {
  const [{ id }] = await db
    .insert(customers)
    .values({
      email,
      name,
      phone: null,
      addressLine1: null,
      addressLine2: null,
      suburb: null,
      state: null,
      postcode: null,
      country: "AU",
      notes: null,
    })
    .onConflictDoUpdate({ target: customers.email, set: { name } })
    .returning({ id: customers.id });
  return id;
}

/* ---------------------------------------------------------------------------
   Discounts
--------------------------------------------------------------------------- */

export function listDiscounts() {
  return db.query.discounts.findMany({
    orderBy: (d, { desc: desc2 }) => desc2(d.createdAt),
  });
}

export interface DiscountInput {
  code: string;
  type: DiscountType;
  value: number;
  active: boolean;
  startsAt: Date | null;
  expiresAt: Date | null;
  usageLimit: number | null;
}

export async function createDiscount(data: DiscountInput) {
  const [{ id }] = await db.insert(discounts).values(data).returning({ id: discounts.id });
  return id;
}

export async function updateDiscount(id: string, data: DiscountInput) {
  await db
    .update(discounts)
    .set({ ...data, updatedAt: new Date() })
    .where(eq(discounts.id, id));
}

export async function deleteDiscount(id: string) {
  await db.delete(discounts).where(eq(discounts.id, id));
}

/** Read-only check for the checkout code-entry preview — same validity rules
 * as redeemDiscountByCode below, but doesn't touch timesUsed. A code that
 * passes this can still fail redemption a moment later (exhausted by someone
 * else, expired mid-checkout); the preview is a convenience, not a promise. */
export async function findValidDiscountByCode(code: string) {
  const now = new Date();
  const discount = await db.query.discounts.findFirst({
    where: and(eq(discounts.code, code.trim().toUpperCase()), eq(discounts.active, true)),
  });
  if (!discount) return null;
  if (discount.startsAt && discount.startsAt > now) return null;
  if (discount.expiresAt && discount.expiresAt < now) return null;
  if (discount.usageLimit !== null && discount.timesUsed >= discount.usageLimit) return null;
  return discount;
}

/** Atomically validates and redeems a discount code in one statement — the
 * WHERE clause carries every validity check, so two concurrent checkouts
 * racing for the last use of a limited code can't both succeed (a
 * read-then-write version of this would let exactly that happen). Called
 * once, from order creation, never from the preview endpoint. */
export async function redeemDiscountByCode(
  code: string,
): Promise<{ id: string; type: DiscountType; value: number } | null> {
  const now = new Date();
  const rows = await db.execute<{ id: string; type: DiscountType; value: number }>(sql`
    UPDATE discounts
    SET times_used = times_used + 1, updated_at = now()
    WHERE code = ${code.trim().toUpperCase()}
      AND active = true
      AND (starts_at IS NULL OR starts_at <= ${now})
      AND (expires_at IS NULL OR expires_at >= ${now})
      AND (usage_limit IS NULL OR times_used < usage_limit)
    RETURNING id, type, value
  `);
  return rows[0] ?? null;
}

/* ---------------------------------------------------------------------------
   Orders. Two sources: a manual "record a phone/email order" path from
   /orders/new, and the storefront's checkout, which reaches these through
   admin/src/app/api/internal/orders (never this module directly — the
   storefront is a separate Next.js app with no access to this database; see
   that route's own comment for why it exists and how it's authenticated).
--------------------------------------------------------------------------- */

export function listOrders() {
  return db.query.orders.findMany({
    with: { customer: true },
    orderBy: (o, { desc: d }) => d(o.createdAt),
  });
}

export function getOrder(id: string) {
  return db.query.orders.findFirst({
    where: eq(orders.id, id),
    with: { customer: true, discount: true, items: true },
  });
}

/** SF-1000 -> 1, the inverse of orderReference below. Null for anything that
 * doesn't parse — callers treat that the same as "not found" rather than a
 * 500, since it's just as likely to be a customer mistyping as an attack. */
export function parseOrderReference(reference: string): number | null {
  const match = reference.trim().toUpperCase().match(/^SF-?(\d+)$/);
  if (!match) return null;
  const seq = Number(match[1]) - 999;
  return seq > 0 ? seq : null;
}

/** Customer-facing order lookup — requires both the reference AND the exact
 * email on the order, not just a guessable sequential number, since order
 * references alone (SF-1000, SF-1001, ...) give no protection against
 * someone paging through other customers' orders. */
export async function findOrderForCustomer(reference: string, email: string) {
  const seq = parseOrderReference(reference);
  if (seq === null) return null;

  const order = await db.query.orders.findFirst({
    where: eq(orders.orderSeq, seq),
    with: { customer: true, items: true },
  });
  if (!order || !order.customer) return null;
  if (order.customer.email.trim().toLowerCase() !== email.trim().toLowerCase()) return null;

  return order;
}

export interface OrderItemInput {
  productId: string | null;
  productName: string;
  colourName: string | null;
  size: string | null;
  quantity: number;
  unitPriceCents: number;
}

export interface OrderInput {
  customerId: string | null;
  status: OrderStatus;
  discountId: string | null;
  discountCents: number;
  shippingCents: number;
  shippingAddress: string | null;
  notes: string | null;
  items: OrderItemInput[];
}

/** Display reference, e.g. SF-1000. `order_seq` starts at 1 -- offsetting by
 * 999 keeps the first real order from reading as suspiciously small. */
export function orderReference(orderSeq: number): string {
  return `SF-${String(orderSeq + 999)}`;
}

/** Line items for one order by internal id -- used by the storefront's
 * TikTok Purchase event (src/lib/tiktok-events.ts) to attach a per-product
 * content_id, never by anything customer-facing (see findOrderForCustomer
 * for that path, which additionally checks the order belongs to the caller). */
export async function getOrderItemsById(id: string) {
  const order = await db.query.orders.findFirst({ where: eq(orders.id, id), with: { items: true } });
  return order?.items ?? null;
}

export async function createOrder(data: OrderInput) {
  const subtotalCents = data.items.reduce((sum, item) => sum + item.quantity * item.unitPriceCents, 0);
  const totalCents = Math.max(0, subtotalCents - data.discountCents + data.shippingCents);

  return db.transaction(async (tx) => {
    const [{ id }] = await tx
      .insert(orders)
      .values({
        customerId: data.customerId,
        status: data.status,
        subtotalCents,
        discountCents: data.discountCents,
        shippingCents: data.shippingCents,
        totalCents,
        discountId: data.discountId,
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

/** The only path that should ever move an order into "paid" — called by the
 * storefront's Stripe webhook, and by staff manually flipping status in
 * admin. Decrements stock for each line that resolves to a real
 * product/colour/size, and sends the order-confirmation email, in the same
 * transition so both happen exactly once alongside the status change.
 *
 * Guarded on the order not already being paid: Stripe retries webhooks, and
 * without this a retried event would decrement stock and re-email twice for
 * one sale. */
export async function markOrderPaid(id: string): Promise<void> {
  const paidOrder = await db.transaction(async (tx) => {
    const order = await tx.query.orders.findFirst({
      where: eq(orders.id, id),
      with: { items: true, customer: true },
    });
    if (!order || order.status === "paid") return null;

    await tx.update(orders).set({ status: "paid", updatedAt: new Date() }).where(eq(orders.id, id));

    for (const item of order.items) {
      if (!item.productId || !item.colourName || !item.size) continue;
      const colour = await tx.query.productColours.findFirst({
        where: and(eq(productColours.productId, item.productId), eq(productColours.name, item.colourName)),
      });
      if (!colour) continue;
      await tx
        .update(colourStock)
        .set({ quantity: sql`${colourStock.quantity} - ${item.quantity}` })
        .where(and(eq(colourStock.colourId, colour.id), eq(colourStock.size, item.size as Size)));
    }

    return order;
  });

  if (!paidOrder || !paidOrder.customer) return;

  try {
    await sendOrderConfirmationEmail({
      toEmail: paidOrder.customer.email,
      toName: paidOrder.customer.name,
      reference: orderReference(paidOrder.orderSeq),
      items: paidOrder.items.map((item) => ({
        productName: item.productName,
        colourName: item.colourName,
        size: item.size,
        quantity: item.quantity,
        unitPriceCents: item.unitPriceCents,
      })),
      subtotalCents: paidOrder.subtotalCents,
      shippingCents: paidOrder.shippingCents,
      totalCents: paidOrder.totalCents,
    });
  } catch (error) {
    // Loud in the logs on purpose, same as the webhook's own order-update
    // failure — a silent email failure means no one ever finds out.
    console.error(`markOrderPaid: failed to send confirmation email for order ${id}`, error);
  }
}

/** Records a tracking number (and optional carrier), and — only the first
 * time a real tracking number is set on this order — sends the shipping
 * confirmation email. Editing an already-set number (a typo fix) updates the
 * record without re-emailing; setting one for the first time always does,
 * independent of the order's status field. */
export async function setOrderTracking(
  id: string,
  trackingNumber: string,
  carrier: string | null,
): Promise<void> {
  const order = await db.query.orders.findFirst({
    where: eq(orders.id, id),
    with: { items: true, customer: true },
  });
  if (!order) throw new Error("Order not found.");

  const cleanTracking = trackingNumber.trim() || null;
  const cleanCarrier = carrier?.trim() || null;
  const isNewTracking = !order.trackingNumber && cleanTracking !== null;

  await db
    .update(orders)
    .set({ trackingNumber: cleanTracking, carrier: cleanCarrier, updatedAt: new Date() })
    .where(eq(orders.id, id));

  if (!isNewTracking || !order.customer) return;

  try {
    await sendShippingConfirmationEmail({
      toEmail: order.customer.email,
      toName: order.customer.name,
      reference: orderReference(order.orderSeq),
      trackingNumber: cleanTracking,
      carrier: cleanCarrier,
      items: order.items.map((item) => ({
        productName: item.productName,
        colourName: item.colourName,
        size: item.size,
        quantity: item.quantity,
      })),
    });
  } catch (error) {
    console.error(`setOrderTracking: failed to send shipping confirmation for order ${id}`, error);
  }
}

/** Cancels an order, refunding the Stripe charge first if money already
 * moved (paid or fulfilled) — cancelling is not just a label change once a
 * customer has actually been charged. Throws rather than silently cancelling
 * without refunding if Stripe isn't configured or the refund itself fails,
 * since that combination (marked cancelled, customer still charged) is worse
 * than leaving the order's status alone. */
export async function cancelOrder(id: string): Promise<void> {
  const order = await db.query.orders.findFirst({ where: eq(orders.id, id) });
  if (!order) throw new Error("Order not found.");

  const moneyHasMoved = order.status === "paid" || order.status === "fulfilled";
  if (moneyHasMoved && order.stripePaymentIntentId) {
    const stripe = getStripe();
    if (!stripe) {
      throw new Error("Can't cancel a paid order — Stripe isn't configured on admin.");
    }
    await stripe.refunds.create({ payment_intent: order.stripePaymentIntentId });
  }

  await db.update(orders).set({ status: "cancelled", updatedAt: new Date() }).where(eq(orders.id, id));
}

const ABANDONED_AFTER_MINUTES = 60;

/** Finds pending orders old enough to count as abandoned and not already
 * emailed, sends each the cart-recovery email, and marks it sent. Called
 * from admin/src/db/notify-abandoned-orders.ts — a script meant to run on a
 * schedule (cron on the box; this repo has no in-process job scheduler),
 * never from a request handler. Returns how many were sent, for that
 * script's own log line. */
export async function notifyAbandonedOrders(): Promise<number> {
  const cutoff = new Date(Date.now() - ABANDONED_AFTER_MINUTES * 60 * 1000);
  const candidates = await db.query.orders.findMany({
    where: and(
      eq(orders.status, "pending"),
      isNull(orders.abandonedEmailSentAt),
      lt(orders.createdAt, cutoff),
    ),
    with: { items: true, customer: true },
  });

  const cartUrl = `${process.env.SITE_URL ?? "https://shirtfaced.wtf"}/cart`;
  let sent = 0;

  for (const order of candidates) {
    if (!order.customer) continue;
    try {
      await sendAbandonedCartEmail({
        toEmail: order.customer.email,
        items: order.items.map((item) => ({
          productName: item.productName,
          colourName: item.colourName,
          size: item.size,
          quantity: item.quantity,
          unitPriceCents: item.unitPriceCents,
        })),
        cartUrl,
      });
      await db
        .update(orders)
        .set({ abandonedEmailSentAt: new Date() })
        .where(eq(orders.id, order.id));
      sent++;
    } catch (error) {
      console.error(`notifyAbandonedOrders: failed to email order ${order.id}`, error);
    }
  }

  return sent;
}

export async function setOrderPaymentIntent(id: string, stripePaymentIntentId: string) {
  await db
    .update(orders)
    .set({ stripePaymentIntentId, updatedAt: new Date() })
    .where(eq(orders.id, id));
}

export async function deleteOrder(id: string) {
  await db.delete(orders).where(eq(orders.id, id));
}

/* ---------------------------------------------------------------------------
   Stock alerts — no new table. `colour_stock` already carries a quantity per
   colour/size; this just names the threshold and does the count.
--------------------------------------------------------------------------- */

export const LOW_STOCK_THRESHOLD = 5;

export interface LowStockRow {
  productId: string;
  productName: string;
  productSlug: string;
  colourName: string;
  size: string;
  quantity: number;
}

/* ---------------------------------------------------------------------------
   Dashboard summary — the numbers worth seeing without going looking for
   them. Revenue counts paid + fulfilled orders only; pending isn't money yet
   and cancelled never was.
--------------------------------------------------------------------------- */

export interface DashboardSummary {
  totalOrders: number;
  pendingOrders: number;
  revenueCents: number;
  customerCount: number;
  activeDiscountCount: number;
  lowStockCount: number;
  recentOrders: {
    id: string;
    orderSeq: number;
    status: OrderStatus;
    totalCents: number;
    customerName: string | null;
    createdAt: Date;
  }[];
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const [[orderStats], [customerStats], [discountStats], lowStock, recentOrders] =
    await Promise.all([
      db.execute<{ total_orders: number; pending_orders: number; revenue_cents: number }>(sql`
        SELECT
          COUNT(*)::int AS total_orders,
          COUNT(*) FILTER (WHERE status = 'pending')::int AS pending_orders,
          COALESCE(SUM(total_cents) FILTER (WHERE status IN ('paid', 'fulfilled')), 0)::int
            AS revenue_cents
        FROM orders
      `),
      db.execute<{ count: number }>(sql`SELECT COUNT(*)::int AS count FROM customers`),
      db.execute<{ count: number }>(
        sql`SELECT COUNT(*)::int AS count FROM discounts WHERE active = true`,
      ),
      listLowStock(),
      db.query.orders.findMany({
        with: { customer: true },
        orderBy: (o, { desc: d }) => d(o.createdAt),
        limit: 5,
      }),
    ]);

  return {
    totalOrders: orderStats.total_orders,
    pendingOrders: orderStats.pending_orders,
    revenueCents: orderStats.revenue_cents,
    customerCount: customerStats.count,
    activeDiscountCount: discountStats.count,
    lowStockCount: lowStock.length,
    recentOrders: recentOrders.map((o) => ({
      id: o.id,
      orderSeq: o.orderSeq,
      status: o.status,
      totalCents: o.totalCents,
      customerName: o.customer?.name ?? null,
      createdAt: o.createdAt,
    })),
  };
}

export async function listLowStock(): Promise<LowStockRow[]> {
  const rows = await db.execute<{
    product_id: string;
    product_name: string;
    product_slug: string;
    colour_name: string;
    size: string;
    quantity: number;
  }>(sql`
    SELECT p.id AS product_id, p.name AS product_name, p.slug AS product_slug,
           pc.name AS colour_name, cs.size, cs.quantity
    FROM colour_stock cs
    JOIN product_colours pc ON pc.id = cs.colour_id
    JOIN products p ON p.id = pc.product_id
    WHERE cs.quantity <= ${LOW_STOCK_THRESHOLD} AND p.published = true
    ORDER BY cs.quantity ASC, p.name ASC
  `);
  return rows.map((r) => ({
    productId: r.product_id,
    productName: r.product_name,
    productSlug: r.product_slug,
    colourName: r.colour_name,
    size: r.size,
    quantity: r.quantity,
  }));
}

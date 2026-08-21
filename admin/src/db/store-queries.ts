import { eq, sql } from "drizzle-orm";
import { db } from "./client";
import {
  customers,
  discounts,
  orderItems,
  orders,
  type DiscountType,
  type OrderStatus,
} from "./schema";

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

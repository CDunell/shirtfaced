import { pgTable, uuid, text, integer, timestamp, jsonb } from "drizzle-orm/pg-core";
import { relations } from "drizzle-orm";

export const CATEGORIES = ["tee", "hoodie", "cap"] as const;
export type Category = (typeof CATEGORIES)[number];

/**
 * Products carry no stock/colour tables the way shirtfaced's schema does —
 * fulfilment is print-on-demand (see ../lib/pod), so there is no physical
 * inventory to track per colour/size. `colours` and `sizes` are small enough
 * (2-3 colours, 4-9 sizes) that a JSON column is honest about that, rather
 * than modelling stock rows for stock that doesn't exist.
 */
export const products = pgTable("products", {
  id: uuid("id").primaryKey().defaultRandom(),
  slug: text("slug").notNull().unique(),
  creature: text("creature").notNull(),
  category: text("category", { enum: CATEGORIES }).notNull(),
  name: text("name").notNull(),
  priceCents: integer("price_cents").notNull(),
  art: text("art").notNull(),
  colours: jsonb("colours").$type<{ name: string; swatch: string; body: string }[]>().notNull(),
  sizes: text("sizes").array().notNull(),
  blurb: text("blurb").notNull(),
  description: text("description").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
});

export const customers = pgTable("customers", {
  id: uuid("id").primaryKey().defaultRandom(),
  email: text("email").notNull().unique(),
  name: text("name").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
});

/* pending -> paid -> in_production -> shipped, or cancelled at any point
   before shipped. "paid" is when lib/pod's createOrder is called (see
   markOrderPaid); "in_production"/"shipped" are driven by the POD provider's
   own webhook (see app/api/pod/webhook) rather than anything staff set by
   hand, once a real provider is wired up. */
export const ORDER_STATUSES = ["pending", "paid", "in_production", "shipped", "cancelled"] as const;
export type OrderStatus = (typeof ORDER_STATUSES)[number];

export const orders = pgTable("orders", {
  id: uuid("id").primaryKey().defaultRandom(),
  /* Human-readable reference, displayed as CS-1000, CS-1001, ... */
  orderSeq: integer("order_seq").notNull().generatedAlwaysAsIdentity(),
  customerId: uuid("customer_id").references(() => customers.id, { onDelete: "set null" }),
  status: text("status", { enum: ORDER_STATUSES }).notNull().default("pending"),
  subtotalCents: integer("subtotal_cents").notNull(),
  shippingCents: integer("shipping_cents").notNull().default(0),
  totalCents: integer("total_cents").notNull(),
  shippingAddress: text("shipping_address"),
  stripePaymentIntentId: text("stripe_payment_intent_id").unique(),
  /* Set once markOrderPaid successfully hands the order to a POD provider
     (see lib/pod/index.ts). Null for any order not yet submitted, including
     everything before payment and anything the POD call failed for. */
  podProvider: text("pod_provider"),
  podOrderId: text("pod_order_id"),
  podStatus: text("pod_status"),
  trackingNumber: text("tracking_number"),
  trackingUrl: text("tracking_url"),
  carrier: text("carrier"),
  /* Staff-facing only, never shown to the customer. Also where a failed POD
     submission is recorded, since there's no separate table for that yet. */
  notes: text("notes"),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
});

export const orderItems = pgTable("order_items", {
  id: uuid("id").primaryKey().defaultRandom(),
  orderId: uuid("order_id")
    .notNull()
    .references(() => orders.id, { onDelete: "cascade" }),
  /* Nullable and paired with a name/colour/size snapshot: a product can be
     edited or deleted after an order ships, and the order has to go on
     describing what was actually sold. */
  productId: uuid("product_id").references(() => products.id, { onDelete: "set null" }),
  productName: text("product_name").notNull(),
  colourName: text("colour_name"),
  size: text("size"),
  quantity: integer("quantity").notNull(),
  unitPriceCents: integer("unit_price_cents").notNull(),
});

export const customersRelations = relations(customers, ({ many }) => ({
  orders: many(orders),
}));

export const ordersRelations = relations(orders, ({ one, many }) => ({
  customer: one(customers, { fields: [orders.customerId], references: [customers.id] }),
  items: many(orderItems),
}));

export const orderItemsRelations = relations(orderItems, ({ one }) => ({
  order: one(orders, { fields: [orderItems.orderId], references: [orders.id] }),
  product: one(products, { fields: [orderItems.productId], references: [products.id] }),
}));

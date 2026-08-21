import {
  pgTable,
  uuid,
  text,
  integer,
  boolean,
  timestamp,
  uniqueIndex,
} from "drizzle-orm/pg-core";
import { relations } from "drizzle-orm";

export const CATEGORIES = [
  "tees",
  "tanks",
  "hoodies",
  "hats",
  "accessories",
] as const;
export type Category = (typeof CATEGORIES)[number];

export const SIZES = ["S", "M", "L", "XL", "XXL"] as const;
export type Size = (typeof SIZES)[number];

export const products = pgTable("products", {
  id: uuid("id").primaryKey().defaultRandom(),
  slug: text("slug").notNull().unique(),
  name: text("name").notNull(),
  category: text("category", { enum: CATEGORIES }).notNull(),
  art: text("art").notNull(),
  priceCents: integer("price_cents").notNull(),
  isNew: boolean("is_new").notNull().default(false),
  blurb: text("blurb").notNull(),
  description: text("description").notNull(),
  /* Live on the storefront once true. Defaults true so every product created
     by hand in this admin behaves exactly as before this column existed —
     only sync-approved-designs.ts inserts a row with this false. Nothing
     price-less or unphotographed reaches a customer by accident. */
  published: boolean("published").notNull().default(true),
  /* Traceability back to Shirtfaced Studio's design pipeline (a separate
     Postgres database and app — see sync-approved-designs.ts). Null for
     products created by hand in this admin, which is most of them today. */
  studioConceptId: uuid("studio_concept_id"),
  studioApprovedDesignId: uuid("studio_approved_design_id").unique(),
  createdAt: timestamp("created_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

export const productColours = pgTable("product_colours", {
  id: uuid("id").primaryKey().defaultRandom(),
  productId: uuid("product_id")
    .notNull()
    .references(() => products.id, { onDelete: "cascade" }),
  name: text("name").notNull(),
  swatch: text("swatch").notNull(),
  body: text("body").notNull(),
  ink: text("ink").notNull(),
  images: text("images").array().notNull().default([]),
  sortOrder: integer("sort_order").notNull().default(0),
});

export const colourStock = pgTable(
  "colour_stock",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    colourId: uuid("colour_id")
      .notNull()
      .references(() => productColours.id, { onDelete: "cascade" }),
    size: text("size", { enum: SIZES }).notNull(),
    quantity: integer("quantity").notNull().default(0),
  },
  (t) => [uniqueIndex("colour_stock_colour_size_idx").on(t.colourId, t.size)],
);

export const productsRelations = relations(products, ({ many }) => ({
  colours: many(productColours),
}));

export const productColoursRelations = relations(
  productColours,
  ({ one, many }) => ({
    product: one(products, {
      fields: [productColours.productId],
      references: [products.id],
    }),
    stock: many(colourStock),
  }),
);

export const colourStockRelations = relations(colourStock, ({ one }) => ({
  colour: one(productColours, {
    fields: [colourStock.colourId],
    references: [productColours.id],
  }),
}));

/* ---------------------------------------------------------------------------
   Site content — one singleton row per page (id is always 1; there is no
   create/delete, only edit). Fields are named per-page to match each page's
   actual layout, not a generic key/value blob — see admin/README.md.
--------------------------------------------------------------------------- */

const singletonId = () => integer("id").primaryKey().default(1);

export const aboutContent = pgTable("about_content", {
  id: singletonId(),
  intro: text("intro").notNull(),
  ideaP1: text("idea_p1").notNull(),
  ideaP2: text("idea_p2").notNull(),
  howMadeP1: text("how_made_p1").notNull(),
  howMadeP2: text("how_made_p2").notNull(),
  wontDoP1: text("wont_do_p1").notNull(),
  whoP1: text("who_p1").notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

export const shippingContent = pgTable("shipping_content", {
  id: singletonId(),
  intro: text("intro").notNull(),
  standardName: text("standard_name").notNull(),
  standardTime: text("standard_time").notNull(),
  standardPrice: text("standard_price").notNull(),
  expressName: text("express_name").notNull(),
  expressTime: text("express_time").notNull(),
  expressPrice: text("express_price").notNull(),
  whereP1: text("where_p1").notNull(),
  whereP2: text("where_p2").notNull(),
  trackingP1: text("tracking_p1").notNull(),
  packagingP1: text("packaging_p1").notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

export const returnsContent = pgTable("returns_content", {
  id: singletonId(),
  intro: text("intro").notNull(),
  step1Title: text("step1_title").notNull(),
  step1Body: text("step1_body").notNull(),
  step2Title: text("step2_title").notNull(),
  step2Body: text("step2_body").notNull(),
  step3Title: text("step3_title").notNull(),
  step3Body: text("step3_body").notNull(),
  step4Title: text("step4_title").notNull(),
  step4Body: text("step4_body").notNull(),
  exchangesP1: text("exchanges_p1").notNull(),
  exchangesP2: text("exchanges_p2").notNull(),
  wrongP1: text("wrong_p1").notNull(),
  wrongP2: text("wrong_p2").notNull(),
  cantTakeP1: text("cant_take_p1").notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

export const contactContent = pgTable("contact_content", {
  id: singletonId(),
  intro: text("intro").notNull(),
  email: text("email").notNull(),
  wholesaleP1: text("wholesale_p1").notNull(),
  pressP1: text("press_p1").notNull(),
  bottomBlurb: text("bottom_blurb").notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

export const sizeGuideContent = pgTable("size_guide_content", {
  id: singletonId(),
  intro: text("intro").notNull(),
  measureChest: text("measure_chest").notNull(),
  measureLength: text("measure_length").notNull(),
  betweenSizesP1: text("between_sizes_p1").notNull(),
  betweenSizesP2: text("between_sizes_p2").notNull(),
  careP1: text("care_p1").notNull(),
  sChest: text("s_chest").notNull(),
  sLength: text("s_length").notNull(),
  mChest: text("m_chest").notNull(),
  mLength: text("m_length").notNull(),
  lChest: text("l_chest").notNull(),
  lLength: text("l_length").notNull(),
  xlChest: text("xl_chest").notNull(),
  xlLength: text("xl_length").notNull(),
  xxlChest: text("xxl_chest").notNull(),
  xxlLength: text("xxl_length").notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

export const homeContent = pgTable("home_content", {
  id: singletonId(),
  trust1: text("trust1").notNull(),
  trust2: text("trust2").notNull(),
  trust3: text("trust3").notNull(),
  promoHeading: text("promo_heading").notNull(),
  promoAlt: text("promo_alt").notNull(),
  newsletterHeading: text("newsletter_heading").notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

export const moreContent = pgTable("more_content", {
  id: singletonId(),
  blurbHeading: text("blurb_heading").notNull(),
  blurbSubline: text("blurb_subline").notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

export const productPageContent = pgTable("product_page_content", {
  id: singletonId(),
  feature1A: text("feature1_a").notNull(),
  feature1B: text("feature1_b").notNull(),
  feature2A: text("feature2_a").notNull(),
  feature2B: text("feature2_b").notNull(),
  feature3A: text("feature3_a").notNull(),
  feature3B: text("feature3_b").notNull(),
  feature4A: text("feature4_a").notNull(),
  feature4B: text("feature4_b").notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

export const accountContent = pgTable("account_content", {
  id: singletonId(),
  intro: text("intro").notNull(),
  benefit1A: text("benefit1_a").notNull(),
  benefit1B: text("benefit1_b").notNull(),
  benefit2A: text("benefit2_a").notNull(),
  benefit2B: text("benefit2_b").notNull(),
  benefit3A: text("benefit3_a").notNull(),
  benefit3B: text("benefit3_b").notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

export const garmentCareContent = pgTable("garment_care_content", {
  id: singletonId(),
  intro: text("intro").notNull(),
  washingP1: text("washing_p1").notNull(),
  dryingP1: text("drying_p1").notNull(),
  printCareP1: text("print_care_p1").notNull(),
  storageP1: text("storage_p1").notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

export const faqContent = pgTable("faq_content", {
  id: singletonId(),
  intro: text("intro").notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

/* A real list, not a singleton — FAQ items vary in count, unlike every
   other content page above. */
export const faqItems = pgTable("faq_items", {
  id: uuid("id").primaryKey().defaultRandom(),
  question: text("question").notNull(),
  answer: text("answer").notNull(),
  /* Optional — most answers that point at another page (shipping, returns,
     size guide, garment care) should link there rather than just say so. */
  linkHref: text("link_href"),
  linkLabel: text("link_label"),
  sortOrder: integer("sort_order").notNull().default(0),
  updatedAt: timestamp("updated_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

/* ---------------------------------------------------------------------------
   Store backend — customers, discounts, orders. Phase 3 of
   docs/ADMIN_STUDIO_UI_OVERHAUL_PLAN.md. Built ahead of checkout landing, so
   the data model and UI exist to receive real orders the moment that ships,
   rather than a second scramble then. No FK from these tables back into
   anything checkout-specific yet, because nothing checkout-specific exists.
--------------------------------------------------------------------------- */

export const customers = pgTable("customers", {
  id: uuid("id").primaryKey().defaultRandom(),
  email: text("email").notNull().unique(),
  name: text("name").notNull(),
  phone: text("phone"),
  addressLine1: text("address_line1"),
  addressLine2: text("address_line2"),
  suburb: text("suburb"),
  state: text("state"),
  postcode: text("postcode"),
  country: text("country").notNull().default("AU"),
  /* Staff-facing only, never shown to the customer. */
  notes: text("notes"),
  createdAt: timestamp("created_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

export const DISCOUNT_TYPES = ["percent", "fixed"] as const;
export type DiscountType = (typeof DISCOUNT_TYPES)[number];

export const discounts = pgTable("discounts", {
  id: uuid("id").primaryKey().defaultRandom(),
  code: text("code").notNull().unique(),
  type: text("type", { enum: DISCOUNT_TYPES }).notNull(),
  /* percent: 0-100. fixed: cents off, same unit as priceCents elsewhere. */
  value: integer("value").notNull(),
  active: boolean("active").notNull().default(true),
  startsAt: timestamp("starts_at", { withTimezone: true }),
  expiresAt: timestamp("expires_at", { withTimezone: true }),
  /* Null means unlimited. */
  usageLimit: integer("usage_limit"),
  timesUsed: integer("times_used").notNull().default(0),
  createdAt: timestamp("created_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

export const ORDER_STATUSES = ["pending", "paid", "fulfilled", "cancelled"] as const;
export type OrderStatus = (typeof ORDER_STATUSES)[number];

export const orders = pgTable("orders", {
  id: uuid("id").primaryKey().defaultRandom(),
  /* A short, sequential, human-readable reference (displayed as SF-1000,
     SF-1001, ...) — a Postgres serial rather than a stored string so it's
     race-free under concurrent inserts and the "next number" is never a
     query away from being wrong. */
  orderSeq: integer("order_seq").notNull().generatedAlwaysAsIdentity(),
  customerId: uuid("customer_id").references(() => customers.id, {
    onDelete: "set null",
  }),
  status: text("status", { enum: ORDER_STATUSES }).notNull().default("pending"),
  subtotalCents: integer("subtotal_cents").notNull(),
  discountCents: integer("discount_cents").notNull().default(0),
  shippingCents: integer("shipping_cents").notNull().default(0),
  totalCents: integer("total_cents").notNull(),
  discountId: uuid("discount_id").references(() => discounts.id, {
    onDelete: "set null",
  }),
  /* Freeform for now — no structured address table exists yet anywhere in
     this schema (customers doesn't get one until an order actually needs
     it), and duplicating one here ahead of real checkout data would be
     guessing at a shape rather than building it. */
  shippingAddress: text("shipping_address"),
  /* Set once the storefront's checkout creates a real Stripe PaymentIntent
     for this order — null for anything entered by hand from /orders/new.
     Looked up by staff in the Stripe dashboard; the webhook that flips
     status to "paid" matches on the PaymentIntent's own metadata, not this
     column, so this is a record, not a join key. */
  stripePaymentIntentId: text("stripe_payment_intent_id").unique(),
  /* Staff-facing only, never shown to the customer. */
  notes: text("notes"),
  createdAt: timestamp("created_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

export const orderItems = pgTable("order_items", {
  id: uuid("id").primaryKey().defaultRandom(),
  orderId: uuid("order_id")
    .notNull()
    .references(() => orders.id, { onDelete: "cascade" }),
  /* Nullable and paired with a name/colour/size snapshot below: a product
     can be edited or deleted after an order ships, and the order has to go
     on describing what was actually sold, not what the catalogue says today. */
  productId: uuid("product_id").references(() => products.id, {
    onDelete: "set null",
  }),
  productName: text("product_name").notNull(),
  colourName: text("colour_name"),
  size: text("size"),
  quantity: integer("quantity").notNull(),
  unitPriceCents: integer("unit_price_cents").notNull(),
});

export const customersRelations = relations(customers, ({ many }) => ({
  orders: many(orders),
}));

export const discountsRelations = relations(discounts, ({ many }) => ({
  orders: many(orders),
}));

export const ordersRelations = relations(orders, ({ one, many }) => ({
  customer: one(customers, {
    fields: [orders.customerId],
    references: [customers.id],
  }),
  discount: one(discounts, {
    fields: [orders.discountId],
    references: [discounts.id],
  }),
  items: many(orderItems),
}));

export const orderItemsRelations = relations(orderItems, ({ one }) => ({
  order: one(orders, {
    fields: [orderItems.orderId],
    references: [orders.id],
  }),
  product: one(products, {
    fields: [orderItems.productId],
    references: [products.id],
  }),
}));

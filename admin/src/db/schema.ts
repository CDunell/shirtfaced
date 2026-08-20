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
  sortOrder: integer("sort_order").notNull().default(0),
  updatedAt: timestamp("updated_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
});

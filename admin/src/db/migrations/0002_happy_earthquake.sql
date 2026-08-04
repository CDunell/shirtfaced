CREATE TABLE "account_content" (
	"id" integer PRIMARY KEY DEFAULT 1 NOT NULL,
	"intro" text NOT NULL,
	"benefit1_a" text NOT NULL,
	"benefit1_b" text NOT NULL,
	"benefit2_a" text NOT NULL,
	"benefit2_b" text NOT NULL,
	"benefit3_a" text NOT NULL,
	"benefit3_b" text NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "home_content" (
	"id" integer PRIMARY KEY DEFAULT 1 NOT NULL,
	"trust1" text NOT NULL,
	"trust2" text NOT NULL,
	"trust3" text NOT NULL,
	"promo_heading" text NOT NULL,
	"promo_alt" text NOT NULL,
	"newsletter_heading" text NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "more_content" (
	"id" integer PRIMARY KEY DEFAULT 1 NOT NULL,
	"blurb_heading" text NOT NULL,
	"blurb_subline" text NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "product_page_content" (
	"id" integer PRIMARY KEY DEFAULT 1 NOT NULL,
	"feature1_a" text NOT NULL,
	"feature1_b" text NOT NULL,
	"feature2_a" text NOT NULL,
	"feature2_b" text NOT NULL,
	"feature3_a" text NOT NULL,
	"feature3_b" text NOT NULL,
	"feature4_a" text NOT NULL,
	"feature4_b" text NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
ALTER TABLE "contact_content" ADD COLUMN "bottom_blurb" text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE "shipping_content" ADD COLUMN "standard_name" text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE "shipping_content" ADD COLUMN "standard_time" text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE "shipping_content" ADD COLUMN "standard_price" text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE "shipping_content" ADD COLUMN "express_name" text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE "shipping_content" ADD COLUMN "express_time" text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE "shipping_content" ADD COLUMN "express_price" text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE "size_guide_content" ADD COLUMN "s_chest" text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE "size_guide_content" ADD COLUMN "s_length" text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE "size_guide_content" ADD COLUMN "m_chest" text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE "size_guide_content" ADD COLUMN "m_length" text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE "size_guide_content" ADD COLUMN "l_chest" text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE "size_guide_content" ADD COLUMN "l_length" text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE "size_guide_content" ADD COLUMN "xl_chest" text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE "size_guide_content" ADD COLUMN "xl_length" text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE "size_guide_content" ADD COLUMN "xxl_chest" text DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE "size_guide_content" ADD COLUMN "xxl_length" text DEFAULT '' NOT NULL;
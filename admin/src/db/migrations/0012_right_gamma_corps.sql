CREATE TABLE "blanks" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"slug" text NOT NULL,
	"brand" text NOT NULL,
	"style_code" text NOT NULL,
	"name" text NOT NULL,
	"category" text NOT NULL,
	"gsm" integer,
	"fit" text,
	"notes" text,
	"sort_order" integer DEFAULT 0 NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "blanks_slug_unique" UNIQUE("slug")
);
--> statement-breakpoint
CREATE TABLE "supplier_offerings" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"supplier_id" uuid NOT NULL,
	"blank_id" uuid NOT NULL,
	"status" text DEFAULT 'unknown' NOT NULL,
	"printed_in" text DEFAULT 'unknown' NOT NULL,
	"max_front" text,
	"max_back" text,
	"max_print_width_mm" integer,
	"max_print_height_mm" integer,
	"standard_print" text,
	"standard_print_width_mm" integer,
	"standard_print_height_mm" integer,
	"price" text,
	"price_cents" integer,
	"standard_price_cents" integer,
	"min_order_qty" integer,
	"source_url" text,
	"verification" text DEFAULT 'not_published' NOT NULL,
	"checked_at" timestamp with time zone,
	"notes" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "suppliers" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"slug" text NOT NULL,
	"name" text NOT NULL,
	"kind" text NOT NULL,
	"location" text,
	"region" text NOT NULL,
	"prints_in" text DEFAULT 'unknown' NOT NULL,
	"methods" text[] DEFAULT '{}' NOT NULL,
	"min_order" text,
	"min_order_qty" integer,
	"max_print" text,
	"max_print_width_mm" integer,
	"max_print_height_mm" integer,
	"standard_print" text,
	"standard_print_width_mm" integer,
	"standard_print_height_mm" integer,
	"website" text,
	"integration" text,
	"has_account" boolean DEFAULT false NOT NULL,
	"source_urls" text[] DEFAULT '{}' NOT NULL,
	"verification" text DEFAULT 'not_published' NOT NULL,
	"checked_at" timestamp with time zone,
	"notes" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "suppliers_slug_unique" UNIQUE("slug")
);
--> statement-breakpoint
ALTER TABLE "supplier_offerings" ADD CONSTRAINT "supplier_offerings_supplier_id_suppliers_id_fk" FOREIGN KEY ("supplier_id") REFERENCES "public"."suppliers"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "supplier_offerings" ADD CONSTRAINT "supplier_offerings_blank_id_blanks_id_fk" FOREIGN KEY ("blank_id") REFERENCES "public"."blanks"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
CREATE UNIQUE INDEX "supplier_offerings_supplier_blank_idx" ON "supplier_offerings" USING btree ("supplier_id","blank_id");
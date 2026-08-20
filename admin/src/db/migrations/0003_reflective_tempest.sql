CREATE TABLE "faq_content" (
	"id" integer PRIMARY KEY DEFAULT 1 NOT NULL,
	"intro" text NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "faq_items" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"question" text NOT NULL,
	"answer" text NOT NULL,
	"sort_order" integer DEFAULT 0 NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "garment_care_content" (
	"id" integer PRIMARY KEY DEFAULT 1 NOT NULL,
	"intro" text NOT NULL,
	"washing_p1" text NOT NULL,
	"drying_p1" text NOT NULL,
	"print_care_p1" text NOT NULL,
	"storage_p1" text NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);

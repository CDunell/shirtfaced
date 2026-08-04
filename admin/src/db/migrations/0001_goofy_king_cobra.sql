CREATE TABLE "about_content" (
	"id" integer PRIMARY KEY DEFAULT 1 NOT NULL,
	"intro" text NOT NULL,
	"idea_p1" text NOT NULL,
	"idea_p2" text NOT NULL,
	"how_made_p1" text NOT NULL,
	"how_made_p2" text NOT NULL,
	"wont_do_p1" text NOT NULL,
	"who_p1" text NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "contact_content" (
	"id" integer PRIMARY KEY DEFAULT 1 NOT NULL,
	"intro" text NOT NULL,
	"email" text NOT NULL,
	"wholesale_p1" text NOT NULL,
	"press_p1" text NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "returns_content" (
	"id" integer PRIMARY KEY DEFAULT 1 NOT NULL,
	"intro" text NOT NULL,
	"step1_title" text NOT NULL,
	"step1_body" text NOT NULL,
	"step2_title" text NOT NULL,
	"step2_body" text NOT NULL,
	"step3_title" text NOT NULL,
	"step3_body" text NOT NULL,
	"step4_title" text NOT NULL,
	"step4_body" text NOT NULL,
	"exchanges_p1" text NOT NULL,
	"exchanges_p2" text NOT NULL,
	"wrong_p1" text NOT NULL,
	"wrong_p2" text NOT NULL,
	"cant_take_p1" text NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "shipping_content" (
	"id" integer PRIMARY KEY DEFAULT 1 NOT NULL,
	"intro" text NOT NULL,
	"where_p1" text NOT NULL,
	"where_p2" text NOT NULL,
	"tracking_p1" text NOT NULL,
	"packaging_p1" text NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "size_guide_content" (
	"id" integer PRIMARY KEY DEFAULT 1 NOT NULL,
	"intro" text NOT NULL,
	"measure_chest" text NOT NULL,
	"measure_length" text NOT NULL,
	"between_sizes_p1" text NOT NULL,
	"between_sizes_p2" text NOT NULL,
	"care_p1" text NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);

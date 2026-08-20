ALTER TABLE "products" ADD COLUMN "published" boolean DEFAULT true NOT NULL;--> statement-breakpoint
ALTER TABLE "products" ADD COLUMN "studio_concept_id" uuid;--> statement-breakpoint
ALTER TABLE "products" ADD COLUMN "studio_approved_design_id" uuid;--> statement-breakpoint
ALTER TABLE "products" ADD CONSTRAINT "products_studio_approved_design_id_unique" UNIQUE("studio_approved_design_id");
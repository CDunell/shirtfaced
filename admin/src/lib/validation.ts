import { z } from "zod";
import { CATEGORIES, SIZES } from "@/db/schema";

export const colourSchema = z.object({
  id: z.string().optional(),
  name: z.string().min(1, "Colour name is required"),
  swatch: z.string().regex(/^#[0-9a-fA-F]{6}$/, "Swatch must be a hex colour"),
  body: z.string().regex(/^#[0-9a-fA-F]{6}$/, "Body must be a hex colour"),
  ink: z.string().regex(/^#[0-9a-fA-F]{6}$/, "Ink must be a hex colour"),
  images: z.array(z.string().min(1)).default([]),
  stock: z.record(z.enum(SIZES), z.coerce.number().int().min(0)),
});

export const productSchema = z.object({
  slug: z
    .string()
    .min(1, "Slug is required")
    .regex(/^[a-z0-9-]+$/, "Slug must be lowercase letters, numbers and hyphens"),
  name: z.string().min(1, "Name is required"),
  category: z.enum(CATEGORIES),
  art: z.string().min(1, "Art key is required"),
  priceCents: z.coerce.number().int().min(0),
  isNew: z.coerce.boolean().default(false),
  published: z.coerce.boolean().default(true),
  blurb: z.string().min(1, "Blurb is required"),
  description: z.string().min(1, "Description is required"),
  colours: z.array(colourSchema).min(1, "Add at least one colourway"),
});

export type ProductInput = z.infer<typeof productSchema>;
export type ColourInput = z.infer<typeof colourSchema>;

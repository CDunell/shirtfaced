import { z } from "zod";

export const DESIGN_STATUSES = [
  "draft",
  "brief_ready",
  "artwork_in_progress",
  "review_ready",
  "revision_required",
  "design_approved",
  "production_review",
  "production_approved",
  "released",
  "rejected",
  "archived",
] as const;

export const GARMENT_TYPES = [
  "tee",
  "hoodie",
  "cap",
  "tank",
  "crop",
  "long_sleeve",
] as const;

export const COLLECTION_ROLES = [
  "core",
  "staple",
  "expression",
  "hero",
  "capsule",
  "collaboration",
] as const;

export const LAYOUT_ARCHETYPES = [
  "small_front_large_back",
  "front_hero_rear_signature",
  "front_hero_clean_back",
  "micro_front_back_hero",
  "unequal_front_back",
  "image_language_split",
  "multi_zone",
  "jumbo_field",
] as const;

export const GRAPHIC_ARCHETYPES = [
  "image_led",
  "type_led",
  "hybrid",
  "emblem",
  "poster",
  "photographic",
  "illustrative",
  "symbolic",
  "collage",
] as const;

export const REVIEW_RESULTS = ["pass", "fail", "not_tested"] as const;

export const designBriefSchema = z.object({
  id: z.string().uuid(),
  title: z.string().trim().min(1),
  version: z.number().int().positive().default(1),
  status: z.enum(DESIGN_STATUSES).default("draft"),
  garment: z.enum(GARMENT_TYPES),
  collectionRole: z.enum(COLLECTION_ROLES),
  layoutArchetype: z.enum(LAYOUT_ARCHETYPES),
  graphicArchetype: z.enum(GRAPHIC_ARCHETYPES),
  dominantProposition: z.string().trim().min(1),
  canonicalBlank: z.string().trim().min(1),
  garmentColour: z.string().trim().min(1),
  printMethod: z.string().trim().min(1),
  permanentRecognitionCues: z.array(z.string().trim().min(1)).min(1),
  assetIds: z.array(z.string().uuid()).default([]),
  createdAt: z.coerce.date(),
  updatedAt: z.coerce.date(),
});

export const hardGateSchema = z.object({
  id: z.string().trim().min(1),
  label: z.string().trim().min(1),
  result: z.enum(REVIEW_RESULTS),
  evidence: z.string().trim().default(""),
});

export const scoreCategorySchema = z.object({
  id: z.string().trim().min(1),
  label: z.string().trim().min(1),
  score: z.number().min(0),
  maximum: z.number().positive(),
  minimumRequired: z.number().min(0).optional(),
  notes: z.string().trim().default(""),
});

export const designReviewSchema = z.object({
  id: z.string().uuid(),
  designId: z.string().uuid(),
  reviewerId: z.string().trim().min(1),
  hardGates: z.array(hardGateSchema),
  scoreCategories: z.array(scoreCategorySchema),
  decision: z.enum([
    "revision_required",
    "design_approved",
    "production_review",
    "production_approved",
    "rejected",
    "archived",
  ]),
  rationale: z.string().trim().min(1),
  createdAt: z.coerce.date(),
});

export type DesignStatus = (typeof DESIGN_STATUSES)[number];
export type GarmentType = (typeof GARMENT_TYPES)[number];
export type CollectionRole = (typeof COLLECTION_ROLES)[number];
export type LayoutArchetype = (typeof LAYOUT_ARCHETYPES)[number];
export type GraphicArchetype = (typeof GRAPHIC_ARCHETYPES)[number];
export type ReviewResult = (typeof REVIEW_RESULTS)[number];
export type DesignBrief = z.infer<typeof designBriefSchema>;
export type HardGate = z.infer<typeof hardGateSchema>;
export type ScoreCategory = z.infer<typeof scoreCategorySchema>;
export type DesignReview = z.infer<typeof designReviewSchema>;

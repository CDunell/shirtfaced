"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { z } from "zod";
import * as queries from "@/db/supplier-queries";
import {
  BLANK_CATEGORIES,
  OFFER_STATUSES,
  PRINT_REGIONS,
  SUPPLIER_KINDS,
  VERIFICATIONS,
} from "@/db/schema";

export type FormState = { error: string | null; saved?: boolean };

const emptyToNull = (v: unknown) => (typeof v === "string" && v.trim() === "" ? null : v);
const optionalText = z.preprocess(emptyToNull, z.string().trim().nullable());
const optionalInt = z.preprocess(
  emptyToNull,
  z.coerce.number().int("Must be a whole number.").min(0).nullable(),
);
/* Dollars as typed, stored as cents. */
const optionalCents = z.preprocess(
  emptyToNull,
  z.coerce
    .number()
    .min(0)
    .transform((v) => Math.round(v * 100))
    .nullable(),
);
/* Centimetres as typed, stored as millimetres. */
const optionalMm = z.preprocess(
  emptyToNull,
  z.coerce
    .number()
    .min(0)
    .transform((v) => Math.round(v * 10))
    .nullable(),
);

const supplierSchema = z.object({
  name: z.string().trim().min(1, "Name can't be empty."),
  kind: z.enum(SUPPLIER_KINDS),
  location: optionalText,
  region: z.string().trim().min(1, "Pick a region."),
  printsIn: z.enum(PRINT_REGIONS),
  methods: z
    .string()
    .default("")
    .transform((v) => v.split(",").map((m) => m.trim()).filter(Boolean)),
  minOrder: optionalText,
  minOrderQty: optionalInt,
  maxPrint: optionalText,
  maxPrintWidthMm: optionalMm,
  maxPrintHeightMm: optionalMm,
  standardPrint: optionalText,
  standardPrintWidthMm: optionalMm,
  standardPrintHeightMm: optionalMm,
  website: optionalText,
  integration: optionalText,
  hasAccount: z.preprocess((v) => v === "on", z.boolean()),
  verification: z.enum(VERIFICATIONS),
  notes: optionalText,
});

export async function updateSupplierAction(
  id: string,
  slug: string,
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const result = supplierSchema.safeParse(Object.fromEntries(formData.entries()));
  if (!result.success) return { error: result.error.issues[0]?.message ?? "Invalid input." };
  try {
    await queries.updateSupplier(id, result.data);
  } catch {
    return { error: "That didn't save. Try again." };
  }
  revalidatePath("/suppliers");
  revalidatePath(`/suppliers/${slug}`);
  return { error: null, saved: true };
}

const offeringSchema = z.object({
  blankId: z.string().uuid("Pick a blank."),
  status: z.enum(OFFER_STATUSES),
  printedIn: z.enum(PRINT_REGIONS),
  maxFront: optionalText,
  maxBack: optionalText,
  maxPrintWidthMm: optionalMm,
  maxPrintHeightMm: optionalMm,
  standardPrint: optionalText,
  standardPrintWidthMm: optionalMm,
  standardPrintHeightMm: optionalMm,
  price: optionalText,
  priceCents: optionalCents,
  standardPriceCents: optionalCents,
  minOrderQty: optionalInt,
  sourceUrl: optionalText,
  verification: z.enum(VERIFICATIONS),
  notes: optionalText,
});

export async function saveOfferingAction(
  supplierId: string,
  slug: string,
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const result = offeringSchema.safeParse(Object.fromEntries(formData.entries()));
  if (!result.success) return { error: result.error.issues[0]?.message ?? "Invalid input." };
  const { blankId, ...input } = result.data;
  try {
    await queries.upsertOffering(supplierId, blankId, input);
  } catch {
    return { error: "That didn't save. Try again." };
  }
  revalidatePath("/suppliers");
  revalidatePath(`/suppliers/${slug}`);
  return { error: null, saved: true };
}

const blankSchema = z.object({
  brand: z.string().trim().min(1, "Brand can't be empty."),
  styleCode: z.string().trim().min(1, "Style code can't be empty."),
  name: z.string().trim().min(1, "Name can't be empty."),
  category: z.enum(BLANK_CATEGORIES),
  gsm: optionalInt,
  fit: optionalText,
  fibre: optionalText,
  yarn: optionalText,
  construction: optionalText,
  dye: optionalText,
  printNotes: optionalText,
  specUrl: optionalText,
  notes: optionalText,
});

function slugify(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

export async function createBlankAction(_prev: FormState, formData: FormData): Promise<FormState> {
  const result = blankSchema.safeParse(Object.fromEntries(formData.entries()));
  if (!result.success) return { error: result.error.issues[0]?.message ?? "Invalid input." };
  const slug = slugify(`${result.data.brand} ${result.data.styleCode}`);
  try {
    await queries.createBlank({ slug, ...result.data });
  } catch (err) {
    const message = err instanceof Error ? err.message : "";
    return {
      error: message.includes("blanks_slug_unique")
        ? "That blank already exists."
        : "That didn't save. Try again.",
    };
  }
  revalidatePath("/suppliers");
  redirect(`/suppliers?blank=${encodeURIComponent(slug)}`);
}

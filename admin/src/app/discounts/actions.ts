"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import * as queries from "@/db/store-queries";
import { DISCOUNT_TYPES } from "@/db/schema";

export type FormState = { error: string | null };

const emptyToNull = (v: unknown) => (typeof v === "string" && v.trim() === "" ? null : v);
const optionalDate = z.preprocess(
  emptyToNull,
  z
    .string()
    .transform((v) => new Date(v))
    .nullable(),
);

const discountSchema = z.object({
  code: z
    .string()
    .trim()
    .toUpperCase()
    .min(1, "Code can't be empty.")
    .regex(/^[A-Z0-9_-]+$/, "Code can only use letters, numbers, - and _."),
  type: z.enum(DISCOUNT_TYPES),
  value: z.coerce.number().int().min(0, "Value can't be negative."),
  active: z.preprocess((v) => v === "on" || v === "true", z.boolean()),
  startsAt: optionalDate,
  expiresAt: optionalDate,
  usageLimit: z.preprocess(emptyToNull, z.coerce.number().int().min(1).nullable()),
});

function friendlyDbError(err: unknown): string {
  const message = err instanceof Error ? err.message : String(err);
  if (message.includes("discounts_code_unique")) {
    return "A discount with that code already exists.";
  }
  return "That didn't save. Try again.";
}

export async function createDiscountAction(
  _prevState: FormState,
  formData: FormData,
): Promise<FormState> {
  const result = discountSchema.safeParse(Object.fromEntries(formData.entries()));
  if (!result.success) return { error: result.error.issues[0]?.message ?? "Invalid input." };

  try {
    await queries.createDiscount(result.data);
  } catch (err) {
    return { error: friendlyDbError(err) };
  }

  revalidatePath("/discounts");
  return { error: null };
}

export async function updateDiscountAction(
  id: string,
  _prevState: FormState,
  formData: FormData,
): Promise<FormState> {
  const result = discountSchema.safeParse(Object.fromEntries(formData.entries()));
  if (!result.success) return { error: result.error.issues[0]?.message ?? "Invalid input." };

  try {
    await queries.updateDiscount(id, result.data);
  } catch (err) {
    return { error: friendlyDbError(err) };
  }

  revalidatePath("/discounts");
  return { error: null };
}

export async function deleteDiscountAction(id: string) {
  await queries.deleteDiscount(id);
  revalidatePath("/discounts");
}

"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { productSchema } from "@/lib/validation";
import * as queries from "@/db/queries";

export type FormState = { error: string | null };

function parsePayload(
  formData: FormData,
): { error: string } | { data: ReturnType<typeof productSchema.parse> } {
  const raw = formData.get("payload");
  if (typeof raw !== "string") return { error: "Missing form payload." };

  let json: unknown;
  try {
    json = JSON.parse(raw);
  } catch {
    return { error: "Malformed form payload." };
  }

  const result = productSchema.safeParse(json);
  if (!result.success) {
    return { error: result.error.issues[0]?.message ?? "Invalid input." };
  }
  return { data: result.data };
}

export async function createProductAction(
  _prevState: FormState,
  formData: FormData,
): Promise<FormState> {
  const parsed = parsePayload(formData);
  if ("error" in parsed) return { error: parsed.error };

  try {
    await queries.createProduct(parsed.data);
  } catch (err) {
    return { error: friendlyDbError(err) };
  }

  revalidatePath("/products");
  redirect("/products");
}

export async function updateProductAction(
  id: string,
  _prevState: FormState,
  formData: FormData,
): Promise<FormState> {
  const parsed = parsePayload(formData);
  if ("error" in parsed) return { error: parsed.error };

  try {
    await queries.updateProduct(id, parsed.data);
  } catch (err) {
    return { error: friendlyDbError(err) };
  }

  revalidatePath("/products");
  revalidatePath(`/products/${id}`);
  redirect("/products");
}

export async function deleteProductAction(id: string) {
  await queries.deleteProduct(id);
  revalidatePath("/products");
}

function friendlyDbError(err: unknown): string {
  const message = err instanceof Error ? err.message : String(err);
  if (message.includes("products_slug_unique")) {
    return "That slug is already in use by another product.";
  }
  return "Something went wrong saving this product.";
}

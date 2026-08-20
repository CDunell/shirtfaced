"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { z } from "zod";
import * as queries from "@/db/store-queries";

export type FormState = { error: string | null };

const emptyToNull = (v: unknown) => (typeof v === "string" && v.trim() === "" ? null : v);
const optionalText = z.preprocess(emptyToNull, z.string().trim().nullable());

const customerSchema = z.object({
  email: z.string().trim().toLowerCase().email("Must be a valid email address."),
  name: z.string().trim().min(1, "Name can't be empty."),
  phone: optionalText,
  addressLine1: optionalText,
  addressLine2: optionalText,
  suburb: optionalText,
  state: optionalText,
  postcode: optionalText,
  country: z.string().trim().min(1).default("AU"),
  notes: optionalText,
});

function friendlyDbError(err: unknown): string {
  const message = err instanceof Error ? err.message : String(err);
  if (message.includes("customers_email_unique")) {
    return "A customer with that email already exists.";
  }
  return "That didn't save. Try again.";
}

export async function createCustomerAction(
  _prevState: FormState,
  formData: FormData,
): Promise<FormState> {
  const result = customerSchema.safeParse(Object.fromEntries(formData.entries()));
  if (!result.success) return { error: result.error.issues[0]?.message ?? "Invalid input." };

  let id: string;
  try {
    id = await queries.createCustomer(result.data);
  } catch (err) {
    return { error: friendlyDbError(err) };
  }

  revalidatePath("/customers");
  redirect(`/customers/${id}`);
}

export async function updateCustomerAction(
  id: string,
  _prevState: FormState,
  formData: FormData,
): Promise<FormState> {
  const result = customerSchema.safeParse(Object.fromEntries(formData.entries()));
  if (!result.success) return { error: result.error.issues[0]?.message ?? "Invalid input." };

  try {
    await queries.updateCustomer(id, result.data);
  } catch (err) {
    return { error: friendlyDbError(err) };
  }

  revalidatePath("/customers");
  return { error: null };
}

export async function deleteCustomerAction(id: string) {
  await queries.deleteCustomer(id);
  revalidatePath("/customers");
}

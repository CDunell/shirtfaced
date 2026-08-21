"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { z } from "zod";
import * as queries from "@/db/store-queries";
import { ORDER_STATUSES } from "@/db/schema";

export type FormState = { error: string | null };

const emptyToNull = (v: unknown) => (typeof v === "string" && v.trim() === "" ? null : v);
const optionalText = z.preprocess(emptyToNull, z.string().trim().nullable());

const orderItemSchema = z.object({
  productId: z.string().uuid().nullable(),
  productName: z.string().trim().min(1, "Every line item needs a product name."),
  colourName: z.string().trim().nullable(),
  size: z.string().trim().nullable(),
  quantity: z.number().int().min(1, "Quantity must be at least 1."),
  unitPriceCents: z.number().int().min(0, "Price can't be negative."),
});

const orderSchema = z.object({
  customerId: z.preprocess(emptyToNull, z.string().uuid().nullable()),
  status: z.enum(ORDER_STATUSES),
  discountId: z.preprocess(emptyToNull, z.string().uuid().nullable()),
  discountCents: z.number().int().min(0),
  shippingCents: z.number().int().min(0),
  shippingAddress: optionalText,
  notes: optionalText,
  items: z.array(orderItemSchema).min(1, "An order needs at least one line item."),
});

export async function createOrderAction(
  _prevState: FormState,
  formData: FormData,
): Promise<FormState> {
  const raw = formData.get("payload");
  if (typeof raw !== "string") return { error: "Missing form payload." };

  let json: unknown;
  try {
    json = JSON.parse(raw);
  } catch {
    return { error: "Malformed form payload." };
  }

  const result = orderSchema.safeParse(json);
  if (!result.success) return { error: result.error.issues[0]?.message ?? "Invalid input." };

  let id: string;
  try {
    id = await queries.createOrder(result.data);
  } catch {
    return { error: "That didn't save. Try again." };
  }

  revalidatePath("/orders");
  redirect(`/orders/${id}`);
}

export async function updateOrderStatusAction(
  id: string,
  status: string,
): Promise<{ error: string | null }> {
  const result = z.enum(ORDER_STATUSES).safeParse(status);
  if (!result.success) return { error: "Invalid status." };

  // "paid" and "cancelled" aren't just label changes — paid decrements stock
  // and sends the confirmation email, cancelled refunds Stripe if money
  // already moved. Both go through the same paths the webhook uses, whether
  // staff triggers them by hand here or Stripe does automatically.
  try {
    if (result.data === "paid") {
      await queries.markOrderPaid(id);
    } else if (result.data === "cancelled") {
      await queries.cancelOrder(id);
    } else {
      await queries.updateOrderStatus(id, result.data);
    }
  } catch (error) {
    return { error: error instanceof Error ? error.message : "That didn't save. Try again." };
  }

  revalidatePath("/orders");
  revalidatePath(`/orders/${id}`);
  return { error: null };
}

export async function deleteOrderAction(id: string) {
  await queries.deleteOrder(id);
  revalidatePath("/orders");
}

export async function setOrderTrackingAction(
  id: string,
  trackingNumber: string,
  carrier: string,
): Promise<{ error: string | null }> {
  if (!trackingNumber.trim()) return { error: "Enter a tracking number." };

  try {
    await queries.setOrderTracking(id, trackingNumber, carrier || null);
  } catch (error) {
    return { error: error instanceof Error ? error.message : "That didn't save. Try again." };
  }

  revalidatePath("/orders");
  revalidatePath(`/orders/${id}`);
  return { error: null };
}

"use server";

import { revalidatePath } from "next/cache";
import { markOrderPaid, cancelOrder, updateOrderStatus } from "@/db/store-queries";
import { getStripe } from "@/lib/stripe";
import { db } from "@/db/client";
import { orders } from "@/db/schema";
import { eq } from "drizzle-orm";

export async function markPaidAction(orderId: string) {
  await markOrderPaid(orderId);
  revalidatePath(`/orders/${orderId}`);
}

export async function cancelOrderAction(orderId: string) {
  const order = await db.query.orders.findFirst({ where: eq(orders.id, orderId) });
  if (order?.stripePaymentIntentId) {
    const stripe = getStripe();
    if (stripe) {
      await stripe.refunds.create({ payment_intent: order.stripePaymentIntentId }).catch((error) => {
        console.error(`cancelOrderAction: refund failed for order ${orderId}`, error);
      });
    }
  }
  await cancelOrder(orderId);
  revalidatePath(`/orders/${orderId}`);
}

export async function markShippedAction(orderId: string) {
  await updateOrderStatus(orderId, "shipped");
  revalidatePath(`/orders/${orderId}`);
}

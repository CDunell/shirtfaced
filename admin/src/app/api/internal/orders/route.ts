import { NextResponse } from "next/server";
import { z } from "zod";
import { verifyInternalRequest } from "@/lib/internal-auth";
import {
  createOrder,
  findProductIdBySlug,
  redeemDiscountByCode,
  upsertCustomerByEmail,
} from "@/db/store-queries";

/**
 * Called by the storefront's checkout — see
 * src/app/api/create-payment-intent/route.ts in the root Next.js app — to
 * create a pending order the moment a Stripe PaymentIntent is about to be
 * created for it, before payment is confirmed. The storefront has no direct
 * database access (its own SHOP_DATABASE_URL is a read-only role, used only
 * at build time — see its .env.example), so this is the only door in.
 *
 * Always creates status "pending". The webhook that later calls PATCH
 * /api/internal/orders/[id] to flip it to "paid" is the only thing that
 * should ever mark an order paid — never this route, and never the client.
 */
const itemSchema = z.object({
  // Not productId directly — the storefront has no direct database access,
  // so it can't hand us its own idea of a product's id. Resolved to a real
  // productId below, against this app's own catalogue.
  slug: z.string().min(1),
  productName: z.string().min(1),
  colourName: z.string().nullable(),
  size: z.string().nullable(),
  quantity: z.number().int().positive(),
  unitPriceCents: z.number().int().nonnegative(),
});

const bodySchema = z.object({
  customer: z.object({
    email: z.string().email(),
    name: z.string().min(1),
  }),
  shippingCents: z.number().int().nonnegative(),
  shippingAddress: z.string().min(1),
  discountCode: z.string().min(1).nullable(),
  items: z.array(itemSchema).min(1),
});

export async function POST(request: Request) {
  if (!verifyInternalRequest(request)) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const json = await request.json().catch(() => null);
  const parsed = bodySchema.safeParse(json);
  if (!parsed.success) {
    return NextResponse.json(
      { error: parsed.error.issues[0]?.message ?? "Invalid request body." },
      { status: 400 },
    );
  }
  const body = parsed.data;

  const customerId = await upsertCustomerByEmail(body.customer.email, body.customer.name);

  const items = await Promise.all(
    body.items.map(async (item) => ({
      productId: await findProductIdBySlug(item.slug),
      productName: item.productName,
      colourName: item.colourName,
      size: item.size,
      quantity: item.quantity,
      unitPriceCents: item.unitPriceCents,
    })),
  );

  // Redeemed here, atomically, rather than trusting a discountCents the
  // storefront computed — that's the only way to enforce usage limits
  // race-free (see redeemDiscountByCode) and it means the amount actually
  // charged (computed by the caller from this response) can't drift from
  // what the code is actually worth.
  let discountId: string | null = null;
  let discountCents = 0;
  if (body.discountCode) {
    const redeemed = await redeemDiscountByCode(body.discountCode);
    if (!redeemed) {
      return NextResponse.json({ error: "That code's no longer valid." }, { status: 400 });
    }
    discountId = redeemed.id;
    const subtotalCents = items.reduce((sum, item) => sum + item.quantity * item.unitPriceCents, 0);
    discountCents =
      redeemed.type === "percent"
        ? Math.round((subtotalCents * redeemed.value) / 100)
        : Math.min(redeemed.value, subtotalCents);
  }

  const orderId = await createOrder({
    customerId,
    status: "pending",
    discountId,
    discountCents,
    shippingCents: body.shippingCents,
    shippingAddress: body.shippingAddress,
    notes: "Created from storefront checkout.",
    items,
  });

  return NextResponse.json({ orderId, discountCents }, { status: 201 });
}

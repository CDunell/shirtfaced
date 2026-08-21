import { NextResponse } from "next/server";
import { z } from "zod";
import { verifyInternalRequest } from "@/lib/internal-auth";
import { findValidDiscountByCode } from "@/db/store-queries";

/**
 * Called by the storefront's checkout when a customer types a discount code,
 * to preview whether it's currently usable and what it looks like — never
 * mutates timesUsed. Real redemption happens once, atomically, inside order
 * creation (see redeemDiscountByCode in store-queries.ts) so a code being
 * exhausted between preview and payment is possible but never double-spent.
 */
const bodySchema = z.object({ code: z.string().min(1) });

export async function POST(request: Request) {
  if (!verifyInternalRequest(request)) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const json = await request.json().catch(() => null);
  const parsed = bodySchema.safeParse(json);
  if (!parsed.success) {
    return NextResponse.json({ error: "Enter a code." }, { status: 400 });
  }

  const discount = await findValidDiscountByCode(parsed.data.code);
  if (!discount) {
    return NextResponse.json({ error: "That code isn't valid." }, { status: 404 });
  }

  return NextResponse.json({
    discount: { code: discount.code, type: discount.type, value: discount.value },
  });
}

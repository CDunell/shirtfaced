import { NextResponse } from "next/server";
import { z } from "zod";
import { verifyInternalRequest } from "@/lib/internal-auth";
import { addNewsletterSubscriber } from "@/db/store-queries";

/**
 * Called by curbstamps-site's homepage signup form — see api/newsletter in
 * that app. The storefront has no direct database access, so this is the
 * only door in, same as /api/internal/orders.
 */
const bodySchema = z.object({
  email: z.string().email(),
  source: z.string().min(1).max(64).default("storefront"),
});

export async function POST(request: Request) {
  if (!verifyInternalRequest(request)) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const json = await request.json().catch(() => null);
  const parsed = bodySchema.safeParse(json);
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.issues[0]?.message ?? "Invalid request body." }, { status: 400 });
  }

  await addNewsletterSubscriber(parsed.data.email, parsed.data.source);

  return NextResponse.json({ ok: true }, { status: 201 });
}

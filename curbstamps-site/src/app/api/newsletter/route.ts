import { NextResponse } from "next/server";

/**
 * Called from the homepage "Join the curb!" form. Forwards the address to
 * curbstamps-admin's internal API (this app has no direct DB access — same
 * split as checkout's create-payment-intent route).
 */
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export async function POST(request: Request) {
  const adminApiUrl = process.env.ADMIN_API_URL;
  const adminApiKey = process.env.ADMIN_INTERNAL_API_KEY;

  if (!adminApiUrl || !adminApiKey) {
    return NextResponse.json({ error: "Signups aren't connected yet.", notConfigured: true }, { status: 503 });
  }

  const json = await request.json().catch(() => null);
  const email = json && typeof json === "object" ? (json as Record<string, unknown>).email : null;
  if (typeof email !== "string" || !EMAIL_PATTERN.test(email.trim())) {
    return NextResponse.json({ error: "That doesn't look like an email address." }, { status: 400 });
  }

  const adminResponse = await fetch(`${adminApiUrl}/api/internal/newsletter`, {
    method: "POST",
    headers: { "content-type": "application/json", "x-internal-api-key": adminApiKey },
    body: JSON.stringify({ email: email.trim(), source: "storefront-home" }),
  }).catch(() => null);

  if (!adminResponse || !adminResponse.ok) {
    return NextResponse.json({ error: "Couldn't save that just now. Try again in a moment." }, { status: 502 });
  }

  return NextResponse.json({ ok: true });
}

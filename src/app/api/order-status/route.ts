import { NextResponse } from "next/server";

/**
 * Proxies to admin's internal order lookup — the storefront has no direct
 * database access (see other routes in this directory for the same note),
 * so every real lookup goes through admin's own API, authenticated with the
 * shared internal key that never reaches the browser.
 */
type RequestBody = { reference: string; email: string };

function isRequestBody(value: unknown): value is RequestBody {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return typeof v.reference === "string" && typeof v.email === "string";
}

export async function POST(request: Request) {
  const adminApiUrl = process.env.ADMIN_API_URL;
  const adminApiKey = process.env.ADMIN_INTERNAL_API_KEY;
  if (!adminApiUrl || !adminApiKey) {
    return NextResponse.json(
      { error: "Order tracking isn't connected yet.", notConfigured: true },
      { status: 503 },
    );
  }

  const json = await request.json().catch(() => null);
  if (!isRequestBody(json)) {
    return NextResponse.json({ error: "Enter an order number and email." }, { status: 400 });
  }

  const lookupResponse = await fetch(`${adminApiUrl}/api/internal/orders/lookup`, {
    method: "POST",
    headers: { "content-type": "application/json", "x-internal-api-key": adminApiKey },
    body: JSON.stringify({ reference: json.reference, email: json.email }),
  });

  const body = await lookupResponse.json().catch(() => ({}));
  if (!lookupResponse.ok) {
    return NextResponse.json(
      { error: body.error ?? "No order found for that number and email." },
      { status: lookupResponse.status },
    );
  }

  return NextResponse.json(body);
}

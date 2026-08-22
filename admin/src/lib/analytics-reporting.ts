import { createSign } from "node:crypto";

/**
 * Server-side reads from GA4, Meta and TikTok's own reporting APIs, so
 * traffic/ad performance shows up on the Analytics page here instead of
 * needing three separate platform logins. Each is independent and returns
 * "not_connected" until its own env vars are set — same convention as every
 * other integration in this app (Stripe, Resend, Studio's database).
 *
 * These are read-only reporting credentials, distinct from the storefront's
 * NEXT_PUBLIC_*_PIXEL_ID and *_ACCESS_TOKEN vars (see ../root .env.example),
 * which only send conversion events — they can't read anything back.
 */

export type Report<T> =
  | { status: "not_connected" }
  | { status: "error"; message: string }
  | { status: "ok"; data: T };

function base64url(input: Buffer | string) {
  return Buffer.from(input)
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

/**
 * Exchanges a GA4 service account's key for a short-lived OAuth access
 * token. Hand-rolled rather than pulling in google-auth-library for one
 * call site — it's a standard RS256-signed JWT exchange, nothing library
 * code buys much over node:crypto plus fetch.
 */
async function getGoogleAccessToken(clientEmail: string, privateKey: string) {
  const now = Math.floor(Date.now() / 1000);
  const header = base64url(JSON.stringify({ alg: "RS256", typ: "JWT" }));
  const claim = base64url(
    JSON.stringify({
      iss: clientEmail,
      scope: "https://www.googleapis.com/auth/analytics.readonly",
      aud: "https://oauth2.googleapis.com/token",
      exp: now + 3600,
      iat: now,
    }),
  );
  const signer = createSign("RSA-SHA256");
  signer.update(`${header}.${claim}`);
  signer.end();
  const signature = base64url(signer.sign(privateKey));

  const res = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer",
      assertion: `${header}.${claim}.${signature}`,
    }),
  });
  if (!res.ok) throw new Error(`Google token exchange failed (${res.status})`);
  const body = (await res.json()) as { access_token: string };
  return body.access_token;
}

export type Ga4Summary = {
  sessions: number;
  activeUsers: number;
  conversions: number;
  revenue: number;
};

export async function fetchGa4Summary(days = 30): Promise<Report<Ga4Summary>> {
  const propertyId = process.env.GA4_PROPERTY_ID;
  const clientEmail = process.env.GA4_SERVICE_ACCOUNT_EMAIL;
  const privateKey = process.env.GA4_SERVICE_ACCOUNT_PRIVATE_KEY?.replace(/\\n/g, "\n");
  if (!propertyId || !clientEmail || !privateKey) return { status: "not_connected" };

  try {
    const accessToken = await getGoogleAccessToken(clientEmail, privateKey);
    const res = await fetch(
      `https://analyticsdata.googleapis.com/v1beta/properties/${propertyId}:runReport`,
      {
        method: "POST",
        headers: { "content-type": "application/json", authorization: `Bearer ${accessToken}` },
        body: JSON.stringify({
          dateRanges: [{ startDate: `${days}daysAgo`, endDate: "today" }],
          metrics: [
            { name: "sessions" },
            { name: "activeUsers" },
            { name: "conversions" },
            { name: "totalRevenue" },
          ],
        }),
        next: { revalidate: 3600 },
      },
    );
    if (!res.ok) {
      return { status: "error", message: `GA4 Data API returned ${res.status}: ${await res.text()}` };
    }
    const body = (await res.json()) as {
      rows?: Array<{ metricValues?: Array<{ value?: string }> }>;
    };
    const values = body.rows?.[0]?.metricValues ?? [];
    return {
      status: "ok",
      data: {
        sessions: Number(values[0]?.value ?? 0),
        activeUsers: Number(values[1]?.value ?? 0),
        conversions: Number(values[2]?.value ?? 0),
        revenue: Number(values[3]?.value ?? 0),
      },
    };
  } catch (error) {
    return { status: "error", message: (error as Error).message };
  }
}

export type AdsSummary = {
  spend: number;
  purchaseValue: number;
  roas: number | null;
};

/**
 * A Meta Pixel/Conversions API "Purchase" event can surface in Insights
 * under any of these action_type keys depending on account and reporting
 * setup — omni_purchase is the current unified-events name, the others are
 * older/pixel-only forms still seen on some accounts.
 */
const META_PURCHASE_ACTION_TYPES = ["omni_purchase", "purchase", "offsite_conversion.fb_pixel_purchase"];

export async function fetchMetaAdsSummary(days = 30): Promise<Report<AdsSummary>> {
  const adAccountId = process.env.META_AD_ACCOUNT_ID;
  const accessToken = process.env.META_ADS_READ_ACCESS_TOKEN;
  if (!adAccountId || !accessToken) return { status: "not_connected" };

  try {
    const url = new URL(`https://graph.facebook.com/v21.0/act_${adAccountId}/insights`);
    url.searchParams.set("fields", "spend,actions,action_values");
    url.searchParams.set("date_preset", days <= 7 ? "last_7d" : "last_30d");
    url.searchParams.set("access_token", accessToken);

    const res = await fetch(url, { next: { revalidate: 3600 } });
    if (!res.ok) {
      return { status: "error", message: `Meta Insights API returned ${res.status}: ${await res.text()}` };
    }
    const body = (await res.json()) as {
      data?: Array<{
        spend?: string;
        actions?: Array<{ action_type: string; value: string }>;
        action_values?: Array<{ action_type: string; value: string }>;
      }>;
    };
    const row = body.data?.[0];
    if (!row) return { status: "ok", data: { spend: 0, purchaseValue: 0, roas: null } };

    const spend = Number(row.spend ?? 0);
    const purchaseValue = Number(
      row.action_values?.find((a) => META_PURCHASE_ACTION_TYPES.includes(a.action_type))?.value ?? 0,
    );
    return { status: "ok", data: { spend, purchaseValue, roas: spend > 0 ? purchaseValue / spend : null } };
  } catch (error) {
    return { status: "error", message: (error as Error).message };
  }
}

export async function fetchTikTokAdsSummary(days = 30): Promise<Report<AdsSummary>> {
  const advertiserId = process.env.TIKTOK_ADVERTISER_ID;
  const accessToken = process.env.TIKTOK_ADS_READ_ACCESS_TOKEN;
  if (!advertiserId || !accessToken) return { status: "not_connected" };

  try {
    const endDate = new Date().toISOString().slice(0, 10);
    const startDate = new Date(Date.now() - days * 86_400_000).toISOString().slice(0, 10);

    const url = new URL("https://business-api.tiktok.com/open_api/v1.3/report/integrated/get/");
    url.searchParams.set("advertiser_id", advertiserId);
    url.searchParams.set("report_type", "BASIC");
    url.searchParams.set("data_level", "AUCTION_ADVERTISER");
    url.searchParams.set("dimensions", JSON.stringify(["advertiser_id"]));
    url.searchParams.set("metrics", JSON.stringify(["spend", "complete_payment_roas"]));
    url.searchParams.set("start_date", startDate);
    url.searchParams.set("end_date", endDate);

    const res = await fetch(url, {
      headers: { "Access-Token": accessToken },
      next: { revalidate: 3600 },
    });
    const body = (await res.json()) as {
      code?: number;
      message?: string;
      data?: { list?: Array<{ metrics?: Record<string, string> }> };
    };
    if (!res.ok || body.code !== 0) {
      return { status: "error", message: `TikTok Reports API: ${body.message ?? res.status}` };
    }
    const metrics = body.data?.list?.[0]?.metrics;
    if (!metrics) return { status: "ok", data: { spend: 0, purchaseValue: 0, roas: null } };

    const spend = Number(metrics.spend ?? 0);
    const roas = metrics.complete_payment_roas ? Number(metrics.complete_payment_roas) : null;
    return { status: "ok", data: { spend, purchaseValue: roas ? spend * roas : 0, roas } };
  } catch (error) {
    return { status: "error", message: (error as Error).message };
  }
}

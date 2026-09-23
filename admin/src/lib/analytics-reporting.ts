import { createSign } from "node:crypto";

/**
 * Server-side reads from GA4, Meta, TikTok and Google Ads' own reporting
 * APIs, so traffic/ad performance shows up on the Analytics dashboard here
 * instead of needing four separate platform logins. Each is independent and
 * returns "not_connected" until its own env vars are set — same convention
 * as every other integration in this app (Stripe, Resend, Studio's
 * database).
 *
 * These are read-only reporting credentials, distinct from the storefront's
 * NEXT_PUBLIC_*_PIXEL_ID / *_ACCESS_TOKEN vars (see ../../.env.example) and
 * NEXT_PUBLIC_GOOGLE_ADS_ID (the conversion tag) — those only send events,
 * they can't read anything back.
 *
 * Every fetch function here returns both a `summary` (for the top-line
 * stat) and a `daily` series (for the trend chart) from the same date
 * range, so the dashboard never has to reconcile two independently-fetched
 * numbers that could disagree.
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

function isoDate(d: Date) {
  return d.toISOString().slice(0, 10);
}

/** [since, until] inclusive, `days` long, ending today. */
function dateRange(days: number) {
  const until = new Date();
  const since = new Date(Date.now() - (days - 1) * 86_400_000);
  return { since, until };
}

/**
 * Exchanges a GA4 service account's key for a short-lived OAuth access
 * token. Hand-rolled rather than pulling in google-auth-library for one
 * call site — it's a standard RS256-signed JWT exchange, nothing library
 * code buys much over node:crypto plus fetch.
 */
async function getGoogleAccessToken(clientEmail: string, privateKey: string, scope: string) {
  const now = Math.floor(Date.now() / 1000);
  const header = base64url(JSON.stringify({ alg: "RS256", typ: "JWT" }));
  const claim = base64url(
    JSON.stringify({
      iss: clientEmail,
      scope,
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

// --------------------------------------------------------------------- //
// GA4 — site traffic. Read-only via a service account (Viewer role on the
// property), unlike Ads below which has no service-account option at all.
// --------------------------------------------------------------------- //

export type Ga4Summary = {
  sessions: number;
  activeUsers: number;
  conversions: number;
  revenue: number;
};

export type Ga4DailyPoint = {
  date: string; // YYYY-MM-DD
  sessions: number;
  activeUsers: number;
  conversions: number;
  revenue: number;
};

export type Ga4Report = { summary: Ga4Summary; daily: Ga4DailyPoint[] };

function ga4DateToIso(yyyymmdd: string) {
  if (yyyymmdd.length !== 8) return yyyymmdd;
  return `${yyyymmdd.slice(0, 4)}-${yyyymmdd.slice(4, 6)}-${yyyymmdd.slice(6, 8)}`;
}

export async function fetchGa4Report(days = 30): Promise<Report<Ga4Report>> {
  const propertyId = process.env.GA4_PROPERTY_ID;
  const clientEmail = process.env.GA4_SERVICE_ACCOUNT_EMAIL;
  const privateKey = process.env.GA4_SERVICE_ACCOUNT_PRIVATE_KEY?.replace(/\\n/g, "\n");
  if (!propertyId || !clientEmail || !privateKey) return { status: "not_connected" };

  try {
    const accessToken = await getGoogleAccessToken(
      clientEmail,
      privateKey,
      "https://www.googleapis.com/auth/analytics.readonly",
    );
    const runReport = (body: object) =>
      fetch(`https://analyticsdata.googleapis.com/v1beta/properties/${propertyId}:runReport`, {
        method: "POST",
        headers: { "content-type": "application/json", authorization: `Bearer ${accessToken}` },
        body: JSON.stringify(body),
        next: { revalidate: 3600 },
      });

    const metrics = [
      { name: "sessions" },
      { name: "activeUsers" },
      { name: "conversions" },
      { name: "totalRevenue" },
    ];
    const dateRanges = [{ startDate: `${days}daysAgo`, endDate: "today" }];

    // Two calls, not one: activeUsers is a distinct-visitor count. Summing a
    // per-day breakdown of it would double-count anyone who visited on more
    // than one day, so the top-line total needs GA4's own whole-range
    // count, separate from the daily series used for the trend chart (where
    // each day's own count is correct on its own, just not summable).
    const [summaryRes, dailyRes] = await Promise.all([
      runReport({ dateRanges, metrics }),
      runReport({
        dateRanges,
        dimensions: [{ name: "date" }],
        metrics,
        orderBys: [{ dimension: { dimensionName: "date" } }],
      }),
    ]);

    if (!summaryRes.ok) {
      return { status: "error", message: `GA4 Data API returned ${summaryRes.status}: ${await summaryRes.text()}` };
    }
    if (!dailyRes.ok) {
      return { status: "error", message: `GA4 Data API returned ${dailyRes.status}: ${await dailyRes.text()}` };
    }

    const summaryBody = (await summaryRes.json()) as {
      rows?: Array<{ metricValues?: Array<{ value?: string }> }>;
    };
    const s = summaryBody.rows?.[0]?.metricValues ?? [];
    const summary: Ga4Summary = {
      sessions: Number(s[0]?.value ?? 0),
      activeUsers: Number(s[1]?.value ?? 0),
      conversions: Number(s[2]?.value ?? 0),
      revenue: Number(s[3]?.value ?? 0),
    };

    const dailyBody = (await dailyRes.json()) as {
      rows?: Array<{
        dimensionValues?: Array<{ value?: string }>;
        metricValues?: Array<{ value?: string }>;
      }>;
    };
    const daily: Ga4DailyPoint[] = (dailyBody.rows ?? []).map((row) => ({
      date: ga4DateToIso(row.dimensionValues?.[0]?.value ?? ""),
      sessions: Number(row.metricValues?.[0]?.value ?? 0),
      activeUsers: Number(row.metricValues?.[1]?.value ?? 0),
      conversions: Number(row.metricValues?.[2]?.value ?? 0),
      revenue: Number(row.metricValues?.[3]?.value ?? 0),
    }));

    return { status: "ok", data: { summary, daily } };
  } catch (error) {
    return { status: "error", message: (error as Error).message };
  }
}

// --------------------------------------------------------------------- //
// Shared shape for the three ad platforms below — spend/purchaseValue are
// both additive across days, unlike GA4's activeUsers, so summary here is
// just the sum of daily.
// --------------------------------------------------------------------- //

export type AdsSummary = {
  spend: number;
  purchaseValue: number;
  roas: number | null;
};

export type AdsDailyPoint = { date: string; spend: number; purchaseValue: number };

export type AdsReport = { summary: AdsSummary; daily: AdsDailyPoint[] };

function summariseAdsDaily(daily: AdsDailyPoint[]): AdsSummary {
  const totals = daily.reduce(
    (acc, d) => ({ spend: acc.spend + d.spend, purchaseValue: acc.purchaseValue + d.purchaseValue }),
    { spend: 0, purchaseValue: 0 },
  );
  return { ...totals, roas: totals.spend > 0 ? totals.purchaseValue / totals.spend : null };
}

// --------------------------------------------------------------------- //
// Meta Ads
// --------------------------------------------------------------------- //

/**
 * A Meta Pixel/Conversions API "Purchase" event can surface in Insights
 * under any of these action_type keys depending on account and reporting
 * setup — omni_purchase is the current unified-events name, the others are
 * older/pixel-only forms still seen on some accounts.
 */
const META_PURCHASE_ACTION_TYPES = ["omni_purchase", "purchase", "offsite_conversion.fb_pixel_purchase"];

export async function fetchMetaAdsReport(days = 30): Promise<Report<AdsReport>> {
  const adAccountId = process.env.META_AD_ACCOUNT_ID;
  const accessToken = process.env.META_ADS_READ_ACCESS_TOKEN;
  if (!adAccountId || !accessToken) return { status: "not_connected" };

  try {
    const { since, until } = dateRange(days);
    const url = new URL(`https://graph.facebook.com/v21.0/act_${adAccountId}/insights`);
    url.searchParams.set("fields", "spend,actions,action_values");
    url.searchParams.set("time_range", JSON.stringify({ since: isoDate(since), until: isoDate(until) }));
    url.searchParams.set("time_increment", "1");
    url.searchParams.set("access_token", accessToken);

    const res = await fetch(url, { next: { revalidate: 3600 } });
    if (!res.ok) {
      return { status: "error", message: `Meta Insights API returned ${res.status}: ${await res.text()}` };
    }
    const body = (await res.json()) as {
      data?: Array<{
        date_start?: string;
        spend?: string;
        action_values?: Array<{ action_type: string; value: string }>;
      }>;
    };
    const daily: AdsDailyPoint[] = (body.data ?? []).map((row) => ({
      date: row.date_start ?? "",
      spend: Number(row.spend ?? 0),
      purchaseValue: Number(
        row.action_values?.find((a) => META_PURCHASE_ACTION_TYPES.includes(a.action_type))?.value ?? 0,
      ),
    }));
    return { status: "ok", data: { summary: summariseAdsDaily(daily), daily } };
  } catch (error) {
    return { status: "error", message: (error as Error).message };
  }
}

// --------------------------------------------------------------------- //
// TikTok Ads
// --------------------------------------------------------------------- //

export async function fetchTikTokAdsReport(days = 30): Promise<Report<AdsReport>> {
  const advertiserId = process.env.TIKTOK_ADVERTISER_ID;
  const accessToken = process.env.TIKTOK_ADS_READ_ACCESS_TOKEN;
  if (!advertiserId || !accessToken) return { status: "not_connected" };

  try {
    const { since, until } = dateRange(days);
    const url = new URL("https://business-api.tiktok.com/open_api/v1.3/report/integrated/get/");
    url.searchParams.set("advertiser_id", advertiserId);
    url.searchParams.set("report_type", "BASIC");
    url.searchParams.set("data_level", "AUCTION_ADVERTISER");
    url.searchParams.set("dimensions", JSON.stringify(["stat_time_day"]));
    url.searchParams.set("metrics", JSON.stringify(["spend", "complete_payment_roas"]));
    url.searchParams.set("start_date", isoDate(since));
    url.searchParams.set("end_date", isoDate(until));
    // Default page size is small (10) — this ensures a 90-day request comes
    // back in one page instead of silently truncating the chart.
    url.searchParams.set("page_size", "1000");

    const res = await fetch(url, { headers: { "Access-Token": accessToken }, next: { revalidate: 3600 } });
    const body = (await res.json()) as {
      code?: number;
      message?: string;
      data?: { list?: Array<{ dimensions?: Record<string, string>; metrics?: Record<string, string> }> };
    };
    if (!res.ok || body.code !== 0) {
      return { status: "error", message: `TikTok Reports API: ${body.message ?? res.status}` };
    }
    // No per-day purchase-value metric in TikTok's Basic report — derived
    // from spend * ROAS per day instead, same fallback the original
    // summary-only version of this function used for the 30-day total.
    const daily: AdsDailyPoint[] = (body.data?.list ?? []).map((row) => {
      const spend = Number(row.metrics?.spend ?? 0);
      const roas = row.metrics?.complete_payment_roas ? Number(row.metrics.complete_payment_roas) : null;
      return {
        date: (row.dimensions?.stat_time_day ?? "").slice(0, 10),
        spend,
        purchaseValue: roas ? spend * roas : 0,
      };
    });
    return { status: "ok", data: { summary: summariseAdsDaily(daily), daily } };
  } catch (error) {
    return { status: "error", message: (error as Error).message };
  }
}

// --------------------------------------------------------------------- //
// Google Ads — the actual ads platform (campaign spend/ROAS), distinct
// from GA4 above (site analytics) and from NEXT_PUBLIC_GOOGLE_ADS_ID on the
// storefront (that only sends a Purchase conversion, it can't read
// anything back). Unlike GA4, the Ads API has no service-account option —
// it needs a one-time OAuth consent flow to mint a refresh token; see
// admin/.env.example for the setup steps.
//
// Not verified against a live account — no Google Ads credentials exist in
// this environment to test with. The query shape below (segments.date +
// metrics.cost_micros/conversions_value from the `customer` resource) is
// Google's documented pattern for account-level daily spend; a mismatch
// would surface as this card's "error" status, not a broken build.
// --------------------------------------------------------------------- //

const GOOGLE_ADS_API_VERSION = "v19";

async function getGoogleAdsAccessToken(clientId: string, clientSecret: string, refreshToken: string) {
  const res = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "refresh_token",
      client_id: clientId,
      client_secret: clientSecret,
      refresh_token: refreshToken,
    }),
  });
  if (!res.ok) throw new Error(`Google Ads token refresh failed (${res.status}): ${await res.text()}`);
  const body = (await res.json()) as { access_token: string };
  return body.access_token;
}

export async function fetchGoogleAdsReport(days = 30): Promise<Report<AdsReport>> {
  const developerToken = process.env.GOOGLE_ADS_DEVELOPER_TOKEN;
  const customerId = process.env.GOOGLE_ADS_CUSTOMER_ID;
  const clientId = process.env.GOOGLE_ADS_CLIENT_ID;
  const clientSecret = process.env.GOOGLE_ADS_CLIENT_SECRET;
  const refreshToken = process.env.GOOGLE_ADS_REFRESH_TOKEN;
  if (!developerToken || !customerId || !clientId || !clientSecret || !refreshToken) {
    return { status: "not_connected" };
  }
  // Optional: only set for a customer id that sits under a manager (MCC)
  // account — the manager's own id, not the child account being queried.
  const loginCustomerId = process.env.GOOGLE_ADS_LOGIN_CUSTOMER_ID;

  try {
    const accessToken = await getGoogleAdsAccessToken(clientId, clientSecret, refreshToken);
    const { since, until } = dateRange(days);

    // BETWEEN with explicit dates rather than GAQL's DURING keyword — DURING
    // only accepts a fixed enum (LAST_7_DAYS, LAST_30_DAYS, ...), not an
    // arbitrary day count, and this dashboard's range picker isn't limited
    // to that enum.
    const query = `
      SELECT segments.date, metrics.cost_micros, metrics.conversions_value
      FROM customer
      WHERE segments.date BETWEEN '${isoDate(since)}' AND '${isoDate(until)}'
      ORDER BY segments.date ASC
    `;

    const res = await fetch(
      `https://googleads.googleapis.com/${GOOGLE_ADS_API_VERSION}/customers/${customerId}/googleAds:search`,
      {
        method: "POST",
        headers: {
          "content-type": "application/json",
          authorization: `Bearer ${accessToken}`,
          "developer-token": developerToken,
          ...(loginCustomerId && { "login-customer-id": loginCustomerId }),
        },
        body: JSON.stringify({ query }),
        next: { revalidate: 3600 },
      },
    );
    if (!res.ok) {
      return { status: "error", message: `Google Ads API returned ${res.status}: ${await res.text()}` };
    }
    const body = (await res.json()) as {
      results?: Array<{
        segments?: { date?: string };
        metrics?: { costMicros?: string; conversionsValue?: number };
      }>;
    };
    const daily: AdsDailyPoint[] = (body.results ?? []).map((r) => ({
      date: r.segments?.date ?? "",
      spend: Number(r.metrics?.costMicros ?? 0) / 1_000_000,
      purchaseValue: Number(r.metrics?.conversionsValue ?? 0),
    }));
    return { status: "ok", data: { summary: summariseAdsDaily(daily), daily } };
  } catch (error) {
    return { status: "error", message: (error as Error).message };
  }
}

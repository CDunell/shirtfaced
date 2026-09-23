import Link from "next/link";
import { notFound } from "next/navigation";
import { Card } from "@/components/ui";
import { formatDollars } from "@/lib/money";
import {
  fetchGa4Report,
  fetchMetaAdsReport,
  fetchTikTokAdsReport,
  fetchGoogleAdsReport,
} from "@/lib/analytics-reporting";
import { TrendChart } from "@/components/analytics/TrendChart";
import { CHANNEL_COLORS } from "@/components/analytics/colors";
import { DateRangeTabs, NotConnected, ReportError, Stat, parseDays } from "@/components/analytics/shared";

export const dynamic = "force-dynamic";

const PLATFORM_META = {
  ga4: {
    label: "Site traffic (GA4)",
    color: CHANNEL_COLORS.ga4,
    envVars: ["GA4_PROPERTY_ID", "GA4_SERVICE_ACCOUNT_EMAIL", "GA4_SERVICE_ACCOUNT_PRIVATE_KEY"],
  },
  meta: {
    label: "Meta Ads",
    color: CHANNEL_COLORS.meta,
    envVars: ["META_AD_ACCOUNT_ID", "META_ADS_READ_ACCESS_TOKEN"],
  },
  tiktok: {
    label: "TikTok Ads",
    color: CHANNEL_COLORS.tiktok,
    envVars: ["TIKTOK_ADVERTISER_ID", "TIKTOK_ADS_READ_ACCESS_TOKEN"],
  },
  "google-ads": {
    label: "Google Ads",
    color: CHANNEL_COLORS.googleAds,
    envVars: [
      "GOOGLE_ADS_DEVELOPER_TOKEN",
      "GOOGLE_ADS_CUSTOMER_ID",
      "GOOGLE_ADS_CLIENT_ID",
      "GOOGLE_ADS_CLIENT_SECRET",
      "GOOGLE_ADS_REFRESH_TOKEN",
    ],
  },
} as const;

type PlatformKey = keyof typeof PLATFORM_META;

function isPlatformKey(value: string): value is PlatformKey {
  return value in PLATFORM_META;
}

export default async function PlatformDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ platform: string }>;
  searchParams: Promise<{ days?: string }>;
}) {
  const { platform } = await params;
  if (!isPlatformKey(platform)) notFound();

  const days = parseDays((await searchParams).days);
  const meta = PLATFORM_META[platform];
  const basePath = `/analytics/platform/${platform}`;

  const header = (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div>
        <Link href="/analytics" className="text-[13px] text-ink/50 hover:underline">
          ← Analytics
        </Link>
        <h1 className="display text-[40px]">{meta.label}</h1>
      </div>
      <DateRangeTabs basePath={basePath} days={days} />
    </div>
  );

  // GA4 (sessions/conversions) and the three ad platforms (spend/ROAS) have
  // different report shapes — kept as separate branches with their own
  // concretely-typed fetch call rather than one generic lookup table, so
  // each branch's report type stays exact instead of a loosely-narrowed union.
  if (platform === "ga4") {
    const report = await fetchGa4Report(days);
    return (
      <div className="flex flex-col gap-6">
        {header}
        {report.status === "not_connected" && <Card><NotConnected what={meta.label} envVars={[...meta.envVars]} /></Card>}
        {report.status === "error" && <Card><ReportError message={report.message} /></Card>}
        {report.status === "ok" && (
          <>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <Stat label="Sessions" value={report.data.summary.sessions.toLocaleString("en-AU")} />
              <Stat label="Users" value={report.data.summary.activeUsers.toLocaleString("en-AU")} />
              <Stat label="Conversions" value={report.data.summary.conversions.toLocaleString("en-AU")} />
              <Stat label="Revenue (GA4)" value={formatDollars(report.data.summary.revenue)} />
            </div>
            <Card>
              <TrendChart
                data={report.data.daily.map((d) => ({
                  date: d.date,
                  sessions: d.sessions,
                  conversions: d.conversions,
                }))}
                series={[
                  { key: "sessions", label: "Sessions", color: meta.color },
                  { key: "conversions", label: "Conversions", color: CHANNEL_COLORS.revenue },
                ]}
                height={320}
              />
            </Card>
          </>
        )}
      </div>
    );
  }

  const report =
    platform === "meta"
      ? await fetchMetaAdsReport(days)
      : platform === "tiktok"
        ? await fetchTikTokAdsReport(days)
        : await fetchGoogleAdsReport(days);

  return (
    <div className="flex flex-col gap-6">
      {header}
      {report.status === "not_connected" && <Card><NotConnected what={meta.label} envVars={[...meta.envVars]} /></Card>}
      {report.status === "error" && <Card><ReportError message={report.message} /></Card>}
      {report.status === "ok" && (
        <>
          <div className="grid grid-cols-3 gap-4">
            <Stat label="Spend" value={formatDollars(report.data.summary.spend)} />
            <Stat label="Purchase value" value={formatDollars(report.data.summary.purchaseValue)} />
            <Stat
              label="ROAS"
              value={report.data.summary.roas === null ? "—" : `${report.data.summary.roas.toFixed(1)}×`}
            />
          </div>
          <Card>
            <TrendChart
              data={report.data.daily.map((d) => ({ date: d.date, spend: d.spend, purchaseValue: d.purchaseValue }))}
              series={[
                { key: "spend", label: "Spend", color: meta.color, format: "dollars" },
                { key: "purchaseValue", label: "Purchase value (platform-reported)", color: CHANNEL_COLORS.revenue, format: "dollars" },
              ]}
              height={320}
            />
          </Card>
          <p className="text-[13px] text-ink/50">
            &ldquo;Purchase value&rdquo; here is what {meta.label} itself claims credit for — check the
            channel breakdown on the{" "}
            <Link href={`/analytics?days=${days}`} className="underline">
              main dashboard
            </Link>{" "}
            for what customers actually paid, from real orders.
          </p>
        </>
      )}
    </div>
  );
}

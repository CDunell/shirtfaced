import Link from "next/link";
import { Card } from "@/components/ui";
import { formatCents, formatDollars } from "@/lib/money";
import { getChannelRevenue, UNATTRIBUTED_CHANNEL } from "@/db/store-queries";
import {
  fetchGa4Report,
  fetchMetaAdsReport,
  fetchTikTokAdsReport,
  fetchGoogleAdsReport,
  type AdsReport,
  type Report,
} from "@/lib/analytics-reporting";
import { TrendChart } from "@/components/analytics/TrendChart";
import { Sparkline } from "@/components/analytics/Sparkline";
import { CHANNEL_COLORS } from "@/components/analytics/colors";
import { DateRangeTabs, NotConnected, ReportError, Stat, parseDays } from "@/components/analytics/shared";

export const dynamic = "force-dynamic";

function dailyDates(days: number): string[] {
  const today = new Date();
  return Array.from({ length: days }, (_, i) =>
    new Date(today.getTime() - (days - 1 - i) * 86_400_000).toISOString().slice(0, 10),
  );
}

const AD_PLATFORMS = [
  { key: "meta", label: "Meta Ads", color: CHANNEL_COLORS.meta, envVars: ["META_AD_ACCOUNT_ID", "META_ADS_READ_ACCESS_TOKEN"] },
  { key: "tiktok", label: "TikTok Ads", color: CHANNEL_COLORS.tiktok, envVars: ["TIKTOK_ADVERTISER_ID", "TIKTOK_ADS_READ_ACCESS_TOKEN"] },
  {
    key: "google-ads",
    label: "Google Ads",
    color: CHANNEL_COLORS.googleAds,
    envVars: ["GOOGLE_ADS_DEVELOPER_TOKEN", "GOOGLE_ADS_CUSTOMER_ID", "GOOGLE_ADS_CLIENT_ID", "GOOGLE_ADS_CLIENT_SECRET", "GOOGLE_ADS_REFRESH_TOKEN"],
  },
] as const;

function AdPlatformCard({
  label,
  color,
  href,
  envVars,
  report,
}: {
  label: string;
  color: string;
  href: string;
  envVars: string[];
  report: Report<AdsReport>;
}) {
  return (
    <Link href={href}>
      <Card className="flex flex-col gap-3 hover:bg-white/80">
        <h3 className="display text-[18px]">{label}</h3>
        {report.status === "not_connected" && <NotConnected what={label} envVars={envVars} />}
        {report.status === "error" && <ReportError message={report.message} />}
        {report.status === "ok" && (
          <>
            <div className="grid grid-cols-2 gap-3">
              <Stat label="Spend" value={formatDollars(report.data.summary.spend)} />
              <Stat
                label="ROAS"
                value={report.data.summary.roas === null ? "—" : `${report.data.summary.roas.toFixed(1)}×`}
              />
            </div>
            <Sparkline data={report.data.daily.map((d) => d.spend)} color={color} />
          </>
        )}
      </Card>
    </Link>
  );
}

export default async function AnalyticsPage({
  searchParams,
}: {
  searchParams: Promise<{ days?: string }>;
}) {
  const days = parseDays((await searchParams).days);

  const [ga4, meta, tiktok, googleAds, channelRevenue] = await Promise.all([
    fetchGa4Report(days),
    fetchMetaAdsReport(days),
    fetchTikTokAdsReport(days),
    fetchGoogleAdsReport(days),
    getChannelRevenue(days),
  ]);

  const adReports = { meta, tiktok, "google-ads": googleAds } as const;

  const totalSpend = [meta, tiktok, googleAds].reduce(
    (sum, r) => sum + (r.status === "ok" ? r.data.summary.spend : 0),
    0,
  );
  const totalRevenueCents = channelRevenue.totals.reduce((sum, c) => sum + c.revenueCents, 0);
  const totalRevenue = totalRevenueCents / 100;
  const blendedRoas = totalSpend > 0 ? totalRevenue / totalSpend : null;

  // One row per day in range, spend split by platform plus the real,
  // internal revenue total — the chart that actually answers "is the ad
  // spend working", cross-checked against what customers really paid
  // rather than what each platform claims about itself.
  const dates = dailyDates(days);
  const spendByDate = (report: Report<AdsReport>) => {
    const map = new Map((report.status === "ok" ? report.data.daily : []).map((d) => [d.date, d.spend]));
    return (date: string) => map.get(date) ?? 0;
  };
  const metaSpendOn = spendByDate(meta);
  const tiktokSpendOn = spendByDate(tiktok);
  const googleAdsSpendOn = spendByDate(googleAds);
  const revenueByDate = new Map<string, number>();
  for (const point of channelRevenue.daily) {
    revenueByDate.set(point.date, (revenueByDate.get(point.date) ?? 0) + point.revenueCents / 100);
  }

  const chartData = dates.map((date) => ({
    date,
    revenue: revenueByDate.get(date) ?? 0,
    metaSpend: metaSpendOn(date),
    tiktokSpend: tiktokSpendOn(date),
    googleAdsSpend: googleAdsSpendOn(date),
  }));

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="display text-[40px]">Analytics</h1>
          <p className="mt-1 text-[14px] text-ink/50">
            Every connected channel, aggregated from each platform&apos;s own API plus real order
            revenue — no other tab needed.
          </p>
        </div>
        <DateRangeTabs basePath="/analytics" days={days} />
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Stat label="Ad spend" value={formatDollars(totalSpend)} />
        <Stat label="Real revenue" value={formatCents(totalRevenueCents)} />
        <Stat label="Blended ROAS" value={blendedRoas === null ? "—" : `${blendedRoas.toFixed(1)}×`} />
        <Stat
          label="Sessions (GA4)"
          value={ga4.status === "ok" ? ga4.data.summary.sessions.toLocaleString("en-AU") : "—"}
        />
      </div>

      <Card className="flex flex-col gap-4">
        <h2 className="display text-[20px]">Spend vs. real revenue</h2>
        <TrendChart
          data={chartData}
          series={[
            { key: "revenue", label: "Real revenue", color: CHANNEL_COLORS.revenue, format: "dollars" },
            { key: "metaSpend", label: "Meta spend", color: CHANNEL_COLORS.meta, format: "dollars" },
            { key: "tiktokSpend", label: "TikTok spend", color: CHANNEL_COLORS.tiktok, format: "dollars" },
            { key: "googleAdsSpend", label: "Google Ads spend", color: CHANNEL_COLORS.googleAds, format: "dollars" },
          ]}
          height={320}
        />
      </Card>

      <div className="flex flex-col gap-4">
        <h2 className="display text-[24px]">Site traffic</h2>
        <Link href={`/analytics/platform/ga4?days=${days}`}>
          <Card className="flex flex-col gap-4 hover:bg-white/80">
            {ga4.status === "not_connected" && (
              <NotConnected
                what="Google Analytics"
                envVars={["GA4_PROPERTY_ID", "GA4_SERVICE_ACCOUNT_EMAIL", "GA4_SERVICE_ACCOUNT_PRIVATE_KEY"]}
              />
            )}
            {ga4.status === "error" && <ReportError message={ga4.message} />}
            {ga4.status === "ok" && (
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                <Stat label="Sessions" value={ga4.data.summary.sessions.toLocaleString("en-AU")} />
                <Stat label="Users" value={ga4.data.summary.activeUsers.toLocaleString("en-AU")} />
                <Stat label="Conversions" value={ga4.data.summary.conversions.toLocaleString("en-AU")} />
                <Stat label="Revenue (GA4)" value={formatDollars(ga4.data.summary.revenue)} />
              </div>
            )}
          </Card>
        </Link>
      </div>

      <div className="flex flex-col gap-4">
        <h2 className="display text-[24px]">Ad platforms</h2>
        <div className="grid gap-4 sm:grid-cols-3">
          {AD_PLATFORMS.map((p) => (
            <AdPlatformCard
              key={p.key}
              label={p.label}
              color={p.color}
              href={`/analytics/platform/${p.key}?days=${days}`}
              envVars={[...p.envVars]}
              report={adReports[p.key]}
            />
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-4">
        <h2 className="display text-[24px]">Revenue by channel</h2>
        <p className="text-[13px] text-ink/50">
          Real orders, grouped by first-touch attribution captured at checkout — not self-reported
          by any ad platform.
        </p>
        {channelRevenue.totals.length === 0 ? (
          <Card>
            <p className="text-[14px] text-ink/50">No paid orders in this range.</p>
          </Card>
        ) : (
          <div className="flex flex-col gap-2">
            {channelRevenue.totals.map((c) => (
              <Link key={c.channel} href={`/analytics/channel/${encodeURIComponent(c.channel)}?days=${days}`}>
                <Card className="flex flex-wrap items-center gap-4 hover:bg-white/80">
                  <span className="min-w-[160px] flex-1 text-[14px] font-semibold">
                    {c.channel === UNATTRIBUTED_CHANNEL ? (
                      <span className="text-ink/60">{c.channel}</span>
                    ) : (
                      c.channel
                    )}
                  </span>
                  <span className="text-[13px] text-ink/50">
                    {c.orders} order{c.orders === 1 ? "" : "s"}
                  </span>
                  <span className="font-semibold">{formatCents(c.revenueCents)}</span>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

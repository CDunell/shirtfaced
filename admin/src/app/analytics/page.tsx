import { Card } from "@/components/ui";
import { formatCents } from "@/lib/money";
import {
  fetchGa4Summary,
  fetchMetaAdsSummary,
  fetchTikTokAdsSummary,
  type AdsSummary,
  type Report,
} from "@/lib/analytics-reporting";

export const dynamic = "force-dynamic";

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[12px] font-semibold tracking-wide text-ink/50 uppercase">{label}</p>
      <p className="display text-[28px]">{value}</p>
    </div>
  );
}

function NotConnected({ what, envVars }: { what: string; envVars: string[] }) {
  return (
    <p className="text-[14px] text-ink/50">
      {what} isn&apos;t connected. Set{" "}
      {envVars.map((v, i) => (
        <span key={v}>
          {i > 0 && ", "}
          <code className="rounded bg-paper-2 px-1.5 py-0.5 text-[13px]">{v}</code>
        </span>
      ))}{" "}
      to turn this card on.
    </p>
  );
}

function ReportError({ message }: { message: string }) {
  return (
    <p className="text-[14px] text-coral">
      Couldn&apos;t load this: {message}
    </p>
  );
}

function AdsCard({
  platform,
  report,
  envVars,
}: {
  platform: string;
  report: Report<AdsSummary>;
  envVars: string[];
}) {
  return (
    <Card className="flex flex-col gap-4">
      <h2 className="display text-[20px]">{platform}</h2>
      {report.status === "not_connected" && <NotConnected what={platform} envVars={envVars} />}
      {report.status === "error" && <ReportError message={report.message} />}
      {report.status === "ok" && (
        <div className="grid grid-cols-3 gap-4">
          <Stat label="Spend" value={formatCents(Math.round(report.data.spend * 100))} />
          <Stat
            label="Purchase value"
            value={formatCents(Math.round(report.data.purchaseValue * 100))}
          />
          <Stat
            label="ROAS"
            value={report.data.roas === null ? "—" : `${report.data.roas.toFixed(1)}×`}
          />
        </div>
      )}
    </Card>
  );
}

export default async function AnalyticsPage() {
  const [ga4, meta, tiktok] = await Promise.all([
    fetchGa4Summary(),
    fetchMetaAdsSummary(),
    fetchTikTokAdsSummary(),
  ]);

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="display text-[40px]">Analytics</h1>
        <p className="mt-1 text-[14px] text-ink/50">Last 30 days, pulled straight from each platform.</p>
      </div>

      <Card className="flex flex-col gap-4">
        <h2 className="display text-[20px]">Site traffic (GA4)</h2>
        {ga4.status === "not_connected" && (
          <NotConnected
            what="Google Analytics"
            envVars={["GA4_PROPERTY_ID", "GA4_SERVICE_ACCOUNT_EMAIL", "GA4_SERVICE_ACCOUNT_PRIVATE_KEY"]}
          />
        )}
        {ga4.status === "error" && <ReportError message={ga4.message} />}
        {ga4.status === "ok" && (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <Stat label="Sessions" value={ga4.data.sessions.toLocaleString("en-AU")} />
            <Stat label="Users" value={ga4.data.activeUsers.toLocaleString("en-AU")} />
            <Stat label="Conversions" value={ga4.data.conversions.toLocaleString("en-AU")} />
            <Stat label="Revenue (GA4)" value={formatCents(Math.round(ga4.data.revenue * 100))} />
          </div>
        )}
      </Card>

      <AdsCard
        platform="Meta Ads"
        report={meta}
        envVars={["META_AD_ACCOUNT_ID", "META_ADS_READ_ACCESS_TOKEN"]}
      />

      <AdsCard
        platform="TikTok Ads"
        report={tiktok}
        envVars={["TIKTOK_ADVERTISER_ID", "TIKTOK_ADS_READ_ACCESS_TOKEN"]}
      />
    </div>
  );
}

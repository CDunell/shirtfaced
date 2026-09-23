import Link from "next/link";
import { Card } from "@/components/ui";
import { formatCents, formatDollars } from "@/lib/money";
import { getChannelRevenue, getOrdersByChannel, orderReference, UNATTRIBUTED_CHANNEL } from "@/db/store-queries";
import { TrendChart } from "@/components/analytics/TrendChart";
import { CHANNEL_COLORS } from "@/components/analytics/colors";
import { DateRangeTabs, Stat, parseDays } from "@/components/analytics/shared";

export const dynamic = "force-dynamic";

export default async function ChannelDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ channel: string }>;
  searchParams: Promise<{ days?: string }>;
}) {
  const { channel: encodedChannel } = await params;
  const channel = decodeURIComponent(encodedChannel);
  const days = parseDays((await searchParams).days);
  const basePath = `/analytics/channel/${encodedChannel}`;

  const [{ daily }, orders] = await Promise.all([
    getChannelRevenue(days),
    getOrdersByChannel(channel, days),
  ]);

  const chartData = daily
    .filter((d) => d.channel === channel)
    .sort((a, b) => a.date.localeCompare(b.date))
    .map((d) => ({ date: d.date, revenue: d.revenueCents / 100 }));

  const totalRevenueCents = orders.reduce((sum, o) => sum + o.totalCents, 0);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link href="/analytics" className="text-[13px] text-ink/50 hover:underline">
            ← Analytics
          </Link>
          <h1 className="display text-[32px] sm:text-[40px]">
            {channel === UNATTRIBUTED_CHANNEL ? (
              <span className="text-ink/60">{channel}</span>
            ) : (
              channel
            )}
          </h1>
        </div>
        <DateRangeTabs basePath={basePath} days={days} />
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <Stat label="Real revenue" value={formatCents(totalRevenueCents)} />
        <Stat label="Orders" value={orders.length.toLocaleString("en-AU")} />
        <Stat
          label="Avg. order value"
          value={orders.length > 0 ? formatCents(Math.round(totalRevenueCents / orders.length)) : "—"}
        />
      </div>

      <Card>
        <TrendChart
          data={chartData}
          series={[{ key: "revenue", label: "Revenue", color: CHANNEL_COLORS.revenue, format: "dollars" }]}
          height={280}
        />
      </Card>

      <div className="flex flex-col gap-3">
        <h2 className="display text-[22px]">Orders</h2>
        {orders.length === 0 ? (
          <Card>
            <p className="text-[14px] text-ink/50">No paid orders from this channel in range.</p>
          </Card>
        ) : (
          <div className="flex flex-col gap-2">
            {orders.map((order) => (
              <Link key={order.id} href={`/orders/${order.id}`}>
                <Card className="flex flex-wrap items-center gap-4 hover:bg-white/80">
                  <span className="font-mono text-[13px]">{orderReference(order.orderSeq)}</span>
                  <span className="min-w-[160px] flex-1 text-[13px] text-ink/70">
                    {order.customer?.name ?? "No customer on file"}
                  </span>
                  <span className="text-[13px] text-ink/50">
                    {order.createdAt.toLocaleDateString("en-AU")}
                  </span>
                  <span className="font-semibold">{formatCents(order.totalCents)}</span>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

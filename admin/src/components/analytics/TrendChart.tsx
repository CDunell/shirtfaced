"use client";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from "recharts";

// A format *type*, not a formatter function — this component is rendered
// from server components (the analytics pages), and a function prop can't
// cross that server/client boundary (React Server Components can't
// serialise a function reference into a client component's props).
const FORMATTERS = {
  dollars: (value: number) =>
    new Intl.NumberFormat("en-AU", { style: "currency", currency: "AUD" }).format(value),
  number: (value: number) => value.toLocaleString("en-AU"),
} as const;

export type TrendSeries = {
  key: string;
  label: string;
  color: string;
  /** How to format this series' values in the tooltip. Plain number if omitted. */
  format?: keyof typeof FORMATTERS;
};

/** One shared line/area chart shape for every dashboard chart — takes
 * already-fetched, already-shaped data so it stays a pure presentation
 * component with no knowledge of GA4/Meta/TikTok/Ads/order-revenue shapes. */
export function TrendChart({
  data,
  series,
  height = 280,
}: {
  /** One point per x-axis tick, keyed by `date` plus each series' `key`. */
  data: Array<Record<string, string | number>>;
  series: TrendSeries[];
  height?: number;
}) {
  if (data.length === 0) {
    return (
      <div
        style={{ height }}
        className="flex items-center justify-center text-[13px] text-ink/40"
      >
        No data in this range.
      </div>
    );
  }

  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(13,13,13,0.08)" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: "rgba(13,13,13,0.5)" }}
            tickFormatter={(d: string) => d.slice(5)}
            axisLine={{ stroke: "rgba(13,13,13,0.15)" }}
            tickLine={false}
            minTickGap={24}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "rgba(13,13,13,0.5)" }}
            axisLine={false}
            tickLine={false}
            width={48}
          />
          <Tooltip
            formatter={(value, name) => {
              const s = series.find((s) => s.label === name);
              const n = typeof value === "number" ? value : Number(value ?? 0);
              return [s?.format ? FORMATTERS[s.format](n) : n, name];
            }}
            contentStyle={{
              borderRadius: 12,
              border: "1px solid rgba(13,13,13,0.1)",
              fontSize: 12,
            }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {series.map((s) => (
            <Line
              key={s.key}
              type="monotone"
              dataKey={s.key}
              name={s.label}
              stroke={s.color}
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

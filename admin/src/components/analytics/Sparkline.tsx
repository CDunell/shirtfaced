"use client";

import { LineChart, Line, ResponsiveContainer } from "recharts";

/** A minimal, axis-less trend line for a summary card — the full chart
 * with axes/legend/tooltip lives on each drill-down page (TrendChart.tsx). */
export function Sparkline({ data, color }: { data: number[]; color: string }) {
  const points = data.map((value, i) => ({ i, value }));
  return (
    <div style={{ width: "100%", height: 36 }}>
      <ResponsiveContainer>
        <LineChart data={points}>
          <Line
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

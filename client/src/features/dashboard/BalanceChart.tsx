import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceDot,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { BalancePoint } from "../../api/types";
import { DataTable, TooltipBox } from "../../components/ui/ChartCard";
import { dayLabel, inr, inrCompact, monthLabel, shortDayLabel } from "../../lib/format";

const AXIS_TICK = { fill: "rgb(var(--muted))", fontSize: 11 };
const DAY_MS = 86_400_000;

const toTime = (day: string) =>
  Date.UTC(Number(day.slice(0, 4)), Number(day.slice(5, 7)) - 1, Number(day.slice(8, 10)));
const toDay = (time: number) => new Date(time).toISOString().slice(0, 10);

export function BalanceChart({ points }: { points: BalancePoint[] }) {
  const data = points.map((point) => ({ time: toTime(point.date), balance: point.balance }));
  const last = data[data.length - 1];
  // Month names repeat on a short range, so switch the ticks to days.
  const tickLabel = last.time - data[0].time < 240 * DAY_MS ? shortDayLabel : monthLabel;

  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={data} margin={{ top: 16, right: 64, bottom: 0, left: 0 }}>
        <CartesianGrid vertical={false} stroke="var(--c-grid)" />
        <XAxis
          dataKey="time"
          type="number"
          scale="time"
          domain={["dataMin", "dataMax"]}
          tickFormatter={(time: number) => tickLabel(toDay(time))}
          tick={AXIS_TICK}
          tickLine={false}
          axisLine={{ stroke: "var(--c-axis)" }}
          minTickGap={48}
        />
        <YAxis
          tickFormatter={inrCompact}
          tick={AXIS_TICK}
          tickLine={false}
          axisLine={false}
          width={56}
        />
        <Tooltip
          cursor={{ stroke: "var(--c-axis)" }}
          isAnimationActive={false}
          content={({ active, payload }) =>
            active && payload?.length ? (
              <TooltipBox
                title={dayLabel(toDay(payload[0].payload.time))}
                rows={[
                  {
                    label: "Balance",
                    value: inr(payload[0].payload.balance),
                    color: "var(--c-balance)",
                  },
                ]}
              />
            ) : null
          }
        />
        <Area
          dataKey="balance"
          type="stepAfter"
          stroke="var(--c-balance)"
          strokeWidth={2}
          fill="var(--c-balance)"
          fillOpacity={0.1}
          dot={false}
          activeDot={{ r: 4, stroke: "rgb(var(--surface))", strokeWidth: 2 }}
          animationDuration={300}
        />
        {/* One direct label, on the latest balance. */}
        <ReferenceDot
          x={last.time}
          y={last.balance}
          r={4}
          fill="var(--c-balance)"
          stroke="rgb(var(--surface))"
          strokeWidth={2}
          label={{
            value: inrCompact(last.balance),
            position: "right",
            fill: "rgb(var(--ink))",
            fontSize: 12,
            fontWeight: 600,
          }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

/** Month-end balances: the table twin of the chart. */
export function BalanceTable({ points }: { points: BalancePoint[] }) {
  const monthEnd = new Map<string, number>();
  for (const point of points) monthEnd.set(point.date.slice(0, 7), point.balance);
  return (
    <DataTable
      head={["Month", "Balance at month end"]}
      rows={[...monthEnd].reverse().map(([month, balance]) => [monthLabel(month), inr(balance)])}
    />
  );
}

import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { MonthFlow } from "../../api/types";
import { DataTable, TooltipBox } from "../../components/ui/ChartCard";
import { inr, inrCompact, monthLabel } from "../../lib/format";

const AXIS_TICK = { fill: "rgb(var(--muted))", fontSize: 11 };

// Colour follows the entity everywhere in the app: income is always this aqua, etc.
const SERIES = [
  { key: "income", label: "Income", color: "var(--c-income)" },
  { key: "spending", label: "Spending", color: "var(--c-spending)" },
  { key: "investing", label: "Investing", color: "var(--c-investing)" },
  { key: "tax", label: "Tax", color: "var(--c-tax)" },
] as const;
const NET = { key: "net_savings", label: "Net savings", color: "rgb(var(--ink))" } as const;

export function FlowsLegend() {
  return (
    <ul className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-ink-2">
      {SERIES.map((series) => (
        <li key={series.key} className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-sm" style={{ background: series.color }} />
          {series.label}
        </li>
      ))}
      <li className="flex items-center gap-1.5">
        <span className="h-0.5 w-4 rounded" style={{ background: NET.color }} />
        {NET.label}
      </li>
    </ul>
  );
}

interface Props {
  flows: MonthFlow[];
  onSelectMonth: (month: string) => void;
}

export function MonthlyFlowsChart({ flows, onSelectMonth }: Props) {
  const select = (entry: { month?: string }) => entry.month && onSelectMonth(entry.month);
  const gap = { stroke: "rgb(var(--surface))", strokeWidth: 1 };

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ComposedChart data={flows} margin={{ top: 8, right: 8, bottom: 0, left: 0 }} barGap={2}>
        <CartesianGrid vertical={false} stroke="var(--c-grid)" />
        <XAxis
          dataKey="month"
          tickFormatter={monthLabel}
          tick={AXIS_TICK}
          tickLine={false}
          axisLine={false}
          minTickGap={24}
        />
        <YAxis
          tickFormatter={inrCompact}
          tick={AXIS_TICK}
          tickLine={false}
          axisLine={false}
          width={56}
        />
        <ReferenceLine y={0} stroke="var(--c-axis)" />
        <Tooltip
          cursor={{ fill: "rgb(var(--muted) / 0.12)" }}
          isAnimationActive={false}
          content={({ active, payload, label }) => {
            if (!active || !payload?.length) return null;
            const flow = payload[0].payload as MonthFlow;
            return (
              <TooltipBox
                title={`${monthLabel(String(label))} · click for transactions`}
                rows={[...SERIES, NET]
                  .filter((series) => series.key !== "tax" || flow.tax !== 0)
                  .map((series) => ({
                    label: series.label,
                    value: inr(flow[series.key]),
                    color: series.color,
                  }))}
              />
            );
          }}
        />
        <Bar
          dataKey="income"
          fill="var(--c-income)"
          maxBarSize={24}
          radius={[4, 4, 0, 0]}
          animationDuration={300}
          cursor="pointer"
          onClick={select}
        />
        {/* Where the income went: one stack of the three outflows. */}
        {SERIES.slice(1).map((series) => (
          <Bar
            key={series.key}
            dataKey={series.key}
            stackId="out"
            fill={series.color}
            maxBarSize={24}
            animationDuration={300}
            cursor="pointer"
            onClick={select}
            {...gap}
          />
        ))}
        <Line
          dataKey={NET.key}
          stroke={NET.color}
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, stroke: "rgb(var(--surface))", strokeWidth: 2 }}
          animationDuration={300}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

export function FlowsTable({ flows }: { flows: MonthFlow[] }) {
  return (
    <DataTable
      head={["Month", "Income", "Spending", "Investing", "Tax", "Net savings"]}
      rows={[...flows]
        .reverse()
        .map((flow) => [
          monthLabel(flow.month),
          inr(flow.income),
          inr(flow.spending),
          inr(flow.investing),
          inr(flow.tax),
          inr(flow.net_savings),
        ])}
    />
  );
}

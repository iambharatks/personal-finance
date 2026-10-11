import type { Kpis } from "../../api/types";
import { inr, percent } from "../../lib/format";

interface Tile {
  label: string;
  value: string;
  detail: string;
}

function tiles(k: Kpis): Tile[] {
  const months = `${k.months} month${k.months === 1 ? "" : "s"}`;
  return [
    { label: "Income", value: inr(k.income), detail: `salary and other income, ${months}` },
    { label: "Spending", value: inr(k.spending), detail: "transfers and investments excluded" },
    {
      label: "Net savings",
      value: inr(k.net_savings),
      detail: k.tax > 0 ? `after ${inr(k.tax)} tax` : "income minus spending",
    },
    {
      label: "Savings rate",
      value: percent(k.savings_rate),
      detail: "of income kept",
    },
    {
      label: "Invested",
      value: inr(k.investing),
      detail: `${percent(k.invest_rate)} of income, net of sales`,
    },
    {
      label: "Average monthly spend",
      value: inr(k.avg_monthly_spend),
      detail: `across ${months}`,
    },
    {
      label: "Runway",
      value: k.runway_months == null ? "–" : `${k.runway_months} months`,
      detail: "closing balance ÷ monthly spend",
    },
    { label: "Closing balance", value: inr(k.closing_balance), detail: "at the end of the period" },
  ];
}

export function KpiTiles({ kpis, stale }: { kpis?: Kpis; stale: boolean }) {
  if (!kpis) {
    return (
      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        {Array.from({ length: 8 }, (_, index) => (
          <div key={index} className="h-[92px] animate-pulse rounded-xl bg-line/60" />
        ))}
      </div>
    );
  }
  return (
    <div
      className={`grid grid-cols-2 gap-3 transition-opacity xl:grid-cols-4 ${stale ? "opacity-50" : ""}`}
    >
      {tiles(kpis).map((tile) => (
        <div key={tile.label} className="rounded-xl border border-line bg-surface px-4 py-3">
          <div className="text-xs text-muted">{tile.label}</div>
          <div className="mt-1 text-2xl font-semibold">{tile.value}</div>
          <div className="mt-0.5 truncate text-xs text-muted" title={tile.detail}>
            {tile.detail}
          </div>
        </div>
      ))}
    </div>
  );
}

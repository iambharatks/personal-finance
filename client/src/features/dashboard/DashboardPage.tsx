import { useNavigate } from "react-router-dom";

import { useApiQuery } from "../../api/hooks";
import type { BalancePoint, CategorySpend, Kpis, MonthFlow } from "../../api/types";
import { ChartCard } from "../../components/ui/ChartCard";
import { monthRange } from "../../lib/filters";
import { transactionsLink, useFilters } from "../../lib/useFilters";
import { BalanceChart, BalanceTable } from "./BalanceChart";
import { CategorySpendChart } from "./CategorySpendChart";
import { KpiTiles } from "./KpiTiles";
import { FlowsLegend, FlowsTable, MonthlyFlowsChart } from "./MonthlyFlowsChart";

export function DashboardPage() {
  const { apiParams, globalSearch } = useFilters();
  const navigate = useNavigate();

  const kpis = useApiQuery<Kpis>("/dashboard", apiParams);
  const balance = useApiQuery<BalancePoint[]>("/charts/balance", apiParams);
  const flows = useApiQuery<MonthFlow[]>("/charts/monthly-flows", apiParams);
  const categories = useApiQuery<CategorySpend[]>("/charts/category-spend", apiParams);

  const openMonth = (month: string) =>
    navigate(transactionsLink(globalSearch, { range: "custom", ...monthRange(month) }));

  return (
    <div className="space-y-4">
      {kpis.isError ? (
        <p className="text-sm text-muted">{kpis.error.message}</p>
      ) : (
        <KpiTiles kpis={kpis.data} stale={kpis.isPlaceholderData} />
      )}

      <ChartCard
        title="Balance"
        subtitle="End-of-day balance across the selected accounts"
        loading={balance.isPending}
        stale={balance.isPlaceholderData}
        error={balance.error}
        empty={!balance.data?.length}
        table={balance.data && <BalanceTable points={balance.data} />}
      >
        {balance.data && <BalanceChart points={balance.data} />}
      </ChartCard>

      <ChartCard
        title="Monthly cash flow"
        subtitle="Income beside where it went; the line is what was left"
        legend={<FlowsLegend />}
        loading={flows.isPending}
        stale={flows.isPlaceholderData}
        error={flows.error}
        empty={!flows.data?.length}
        table={flows.data && <FlowsTable flows={flows.data} />}
      >
        {flows.data && <MonthlyFlowsChart flows={flows.data} onSelectMonth={openMonth} />}
      </ChartCard>

      <ChartCard
        title="Spending by category"
        subtitle="Largest first. Click a row to see its transactions."
        loading={categories.isPending}
        stale={categories.isPlaceholderData}
        error={categories.error}
        empty={!categories.data?.length}
      >
        {categories.data && (
          <CategorySpendChart
            rows={categories.data}
            linkFor={(category) => transactionsLink(globalSearch, { category })}
          />
        )}
      </ChartCard>
    </div>
  );
}

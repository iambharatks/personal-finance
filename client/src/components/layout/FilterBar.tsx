import { useAccounts, useMeta } from "../../api/hooks";
import { rangeOptions, type RangeKey } from "../../lib/filters";
import { dayLabel } from "../../lib/format";
import { useFilters } from "../../lib/useFilters";

/** The one filter row. It scopes every tile, chart and table on every page. */
export function FilterBar() {
  const { range, apiParams, update } = useFilters();
  const accounts = useAccounts();
  const meta = useMeta();

  const setRange = (key: RangeKey) => {
    if (key === "custom") {
      // Start the custom range from whatever is on screen now.
      update({
        range: "custom",
        from: apiParams.from ?? meta.data?.min_date,
        to: apiParams.to ?? meta.data?.max_date,
      });
    } else {
      update({ range: key === "all" ? null : key, from: null, to: null });
    }
  };

  const shownFrom = apiParams.from ?? meta.data?.min_date;
  const shownTo = apiParams.to ?? meta.data?.max_date;

  return (
    <div className="sticky top-0 z-20 flex flex-wrap items-center gap-2 border-b border-line bg-surface/95 px-4 py-2.5 backdrop-blur lg:px-6">
      <label className="sr-only" htmlFor="filter-range">
        Period
      </label>
      <select
        id="filter-range"
        className="field"
        value={range}
        onChange={(event) => setRange(event.target.value as RangeKey)}
      >
        {rangeOptions(new Date()).map((option) => (
          <option key={option.key} value={option.key}>
            {option.label}
          </option>
        ))}
      </select>

      {range === "custom" ? (
        <>
          <input
            type="date"
            aria-label="From"
            className="field"
            value={apiParams.from ?? ""}
            onChange={(event) => update({ from: event.target.value })}
          />
          <span className="text-sm text-muted">to</span>
          <input
            type="date"
            aria-label="To"
            className="field"
            value={apiParams.to ?? ""}
            onChange={(event) => update({ to: event.target.value })}
          />
        </>
      ) : (
        shownFrom &&
        shownTo && (
          <span className="text-sm text-muted">
            {dayLabel(shownFrom)} – {dayLabel(shownTo)}
          </span>
        )
      )}

      <label className="sr-only" htmlFor="filter-account">
        Account
      </label>
      <select
        id="filter-account"
        className="field ml-auto"
        value={apiParams.account ?? ""}
        onChange={(event) => update({ account: event.target.value })}
      >
        <option value="">All accounts</option>
        {accounts.data?.map((account) => (
          <option key={account.id} value={account.id}>
            {account.name}
          </option>
        ))}
      </select>
    </div>
  );
}

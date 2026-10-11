import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";

import { isRangeKey, resolveRange, type RangeKey } from "./filters";

/** Filters that follow you from page to page. Everything else is page-specific. */
const GLOBAL_KEYS = ["range", "from", "to", "account"];

export type FilterPatch = Record<string, string | number | boolean | null | undefined>;

/** The URL is the single source of truth for filters; this reads and writes it. */
export function useFilters() {
  const [search, setSearch] = useSearchParams();

  const rangeParam = search.get("range");
  const range: RangeKey = isRangeKey(rangeParam) ? rangeParam : "all";
  const customFrom = search.get("from") ?? undefined;
  const customTo = search.get("to") ?? undefined;
  const accountParam = search.get("account");

  /** What every dashboard and list request sends to the API. */
  const apiParams = useMemo(() => {
    const dates =
      range === "custom" ? { from: customFrom, to: customTo } : resolveRange(range, new Date());
    return { ...dates, account: accountParam ?? undefined };
  }, [range, customFrom, customTo, accountParam]);

  const update = useCallback(
    (patch: FilterPatch) => {
      setSearch(
        (current) => {
          const next = new URLSearchParams(current);
          // Any filter change returns to the first page unless the patch sets one.
          next.delete("page");
          for (const [key, value] of Object.entries(patch)) {
            if (value === null || value === undefined || value === "" || value === false) {
              next.delete(key);
            } else {
              next.set(key, String(value));
            }
          }
          return next;
        },
        { replace: true },
      );
    },
    [setSearch],
  );

  /** Query string holding only the global filters, for links between pages. */
  const globalSearch = useMemo(() => {
    const kept = new URLSearchParams();
    for (const key of GLOBAL_KEYS) {
      const value = search.get(key);
      if (value) kept.set(key, value);
    }
    return kept.toString();
  }, [search]);

  return { search, range, apiParams, update, globalSearch };
}

/** Link to the transactions page, keeping the global filters and adding more. */
export function transactionsLink(globalSearch: string, extra: Record<string, string | number>) {
  const params = new URLSearchParams(globalSearch);
  for (const [key, value] of Object.entries(extra)) params.set(key, String(value));
  return `/transactions?${params.toString()}`;
}

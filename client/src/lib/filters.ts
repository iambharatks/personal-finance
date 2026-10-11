// Date-range presets. Pure functions; the React side lives in useFilters.ts.

export const RANGE_KEYS = [
  "all",
  "this-month",
  "last-3-months",
  "last-6-months",
  "this-year",
  "fy-current",
  "fy-previous",
  "custom",
] as const;
export type RangeKey = (typeof RANGE_KEYS)[number];

export interface DateRange {
  from?: string;
  to?: string;
}

const pad = (n: number) => String(n).padStart(2, "0");

/** Local calendar date as YYYY-MM-DD. */
export const iso = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

const firstOfMonth = (year: number, month: number) => iso(new Date(year, month, 1));
const lastOfMonth = (year: number, month: number) => iso(new Date(year, month + 1, 0));

/** The Indian financial year runs 1 April - 31 March; it is named by its starting year. */
export const fyStartYear = (d: Date) => (d.getMonth() >= 3 ? d.getFullYear() : d.getFullYear() - 1);

export const fyLabel = (startYear: number) => `FY ${startYear}-${pad((startYear + 1) % 100)}`;

export const fyRange = (startYear: number): DateRange => ({
  from: `${startYear}-04-01`,
  to: `${startYear + 1}-03-31`,
});

/** "2025-04" -> the whole of April 2025. */
export function monthRange(month: string): DateRange {
  const year = Number(month.slice(0, 4));
  const index = Number(month.slice(5, 7)) - 1;
  return { from: firstOfMonth(year, index), to: lastOfMonth(year, index) };
}

export function resolveRange(key: RangeKey, today: Date): DateRange {
  const year = today.getFullYear();
  const month = today.getMonth();
  switch (key) {
    case "this-month":
      return { from: firstOfMonth(year, month), to: lastOfMonth(year, month) };
    case "last-3-months": // this month and the two before it
      return { from: firstOfMonth(year, month - 2), to: lastOfMonth(year, month) };
    case "last-6-months":
      return { from: firstOfMonth(year, month - 5), to: lastOfMonth(year, month) };
    case "this-year":
      return { from: `${year}-01-01`, to: `${year}-12-31` };
    case "fy-current":
      return fyRange(fyStartYear(today));
    case "fy-previous":
      return fyRange(fyStartYear(today) - 1);
    default:
      return {};
  }
}

export function rangeOptions(today: Date): { key: RangeKey; label: string }[] {
  const fy = fyStartYear(today);
  return [
    { key: "all", label: "All time" },
    { key: "this-month", label: "This month" },
    { key: "last-3-months", label: "Last 3 months" },
    { key: "last-6-months", label: "Last 6 months" },
    { key: "this-year", label: "This year" },
    { key: "fy-current", label: fyLabel(fy) },
    { key: "fy-previous", label: fyLabel(fy - 1) },
    { key: "custom", label: "Custom range" },
  ];
}

export const isRangeKey = (value: string | null): value is RangeKey =>
  value !== null && (RANGE_KEYS as readonly string[]).includes(value);

import { Link } from "react-router-dom";

import type { CategorySpend } from "../../api/types";
import { inr, percent } from "../../lib/format";

interface Props {
  rows: CategorySpend[];
  linkFor: (categoryId: number) => string;
}

/** Ranked bars in one colour: the categories have no order of their own, so hue would
 *  add nothing that length does not already say. Each row links to its transactions. */
export function CategorySpendChart({ rows, linkFor }: Props) {
  const largest = rows[0]?.total ?? 1;
  return (
    <ol className="space-y-0.5">
      {rows.map((row) => (
        <li key={row.category_id}>
          <Link
            to={linkFor(row.category_id)}
            title={`${row.count} payments · ${percent(row.share)} of spending`}
            className="group grid grid-cols-[minmax(0,15rem)_minmax(0,1fr)_6.5rem_3rem] items-center gap-3 rounded-md px-2 py-1.5 text-sm hover:bg-page focus-visible:bg-page focus-visible:outline-none"
          >
            <span className="truncate text-ink-2 group-hover:text-ink">
              <span className="mr-2 inline-block w-5 text-center" aria-hidden>
                {row.icon}
              </span>
              {row.name}
            </span>
            <span className="h-2.5">
              <span
                className="block h-full rounded-r"
                style={{
                  width: `${Math.max((row.total / largest) * 100, 0.5)}%`,
                  background: "var(--c-spending)",
                }}
              />
            </span>
            <span className="text-right font-medium tabular-nums">{inr(row.total)}</span>
            <span className="text-right text-xs tabular-nums text-muted">
              {percent(row.share, 0)}
            </span>
          </Link>
        </li>
      ))}
    </ol>
  );
}

import { useState, type ReactNode } from "react";

interface Props {
  title: string;
  subtitle?: string;
  legend?: ReactNode;
  /** The same data as a table. Every chart offers one, so no value is hover-only. */
  table?: ReactNode;
  loading: boolean;
  /** True while newer data is on its way; the old render stays, dimmed. */
  stale?: boolean;
  error?: Error | null;
  empty?: boolean;
  children: ReactNode;
}

export function ChartCard({
  title,
  subtitle,
  legend,
  table,
  loading,
  stale,
  error,
  empty,
  children,
}: Props) {
  const [showTable, setShowTable] = useState(false);

  let body: ReactNode;
  if (error) body = <p className="py-10 text-center text-sm text-muted">{error.message}</p>;
  else if (loading) body = <div className="h-64 animate-pulse rounded-md bg-line/60" />;
  else if (empty) {
    body = <p className="py-10 text-center text-sm text-muted">Nothing in this period.</p>;
  } else {
    body = (
      <div className={stale ? "opacity-50 transition-opacity" : "transition-opacity"}>
        {showTable && table ? <div className="max-h-80 overflow-auto">{table}</div> : children}
      </div>
    );
  }

  return (
    <section className="rounded-xl border border-line bg-surface p-4">
      <header className="mb-3 flex flex-wrap items-start gap-x-4 gap-y-2">
        <div className="mr-auto">
          <h2 className="text-sm font-semibold">{title}</h2>
          {subtitle && <p className="text-xs text-muted">{subtitle}</p>}
        </div>
        {!showTable && legend}
        {table && (
          <button
            className="text-xs text-muted underline-offset-2 hover:text-ink hover:underline"
            onClick={() => setShowTable((shown) => !shown)}
          >
            {showTable ? "Show chart" : "Show table"}
          </button>
        )}
      </header>
      {body}
    </section>
  );
}

/** Small table used for the chart twins. */
export function DataTable({ head, rows }: { head: string[]; rows: (string | number)[][] }) {
  return (
    <table className="w-full text-sm tabular-nums">
      <thead className="sticky top-0 bg-surface text-xs text-muted">
        <tr>
          {head.map((cell, index) => (
            <th key={cell} className={`py-1.5 font-medium ${index ? "text-right" : "text-left"}`}>
              {cell}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row[0]} className="border-t border-line">
            {row.map((cell, index) => (
              <td key={index} className={`py-1.5 ${index ? "text-right" : "text-left"}`}>
                {cell}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** Tooltip shell shared by the charts: the value leads, the series name follows. */
export function TooltipBox({
  title,
  rows,
}: {
  title: string;
  rows: { label: string; value: string; color?: string }[];
}) {
  return (
    <div className="rounded-lg border border-line bg-surface px-3 py-2 text-xs shadow-lg">
      <div className="mb-1 font-medium text-ink-2">{title}</div>
      {rows.map((row) => (
        <div key={row.label} className="flex items-center gap-2 py-0.5">
          <span
            className="h-0.5 w-3 shrink-0 rounded"
            style={{ background: row.color ?? "transparent" }}
          />
          <span className="font-semibold tabular-nums text-ink">{row.value}</span>
          <span className="text-muted">{row.label}</span>
        </div>
      ))}
    </div>
  );
}

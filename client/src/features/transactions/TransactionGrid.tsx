import { createColumnHelper, flexRender, getCoreRowModel, useReactTable } from "@tanstack/react-table";
import { useMemo } from "react";

import type { Category, Txn, TxnPatch } from "../../api/types";
import { dayLabel, inrExact } from "../../lib/format";
import { EditableCategory, EditableText } from "./EditableCell";

const column = createColumnHelper<Txn>();

/** Out of the ordinary rows get a faint tint; the text itself always says why. */
function rowTint(txn: Txn): string {
  if (txn.is_fallback) return "bg-amber-400/10";
  if (txn.kind === "income") return "bg-emerald-500/10";
  if (txn.kind === "expense" && txn.money_out >= 10000) return "bg-rose-500/10";
  return "";
}

const money = (value: number) => (value ? inrExact(value) : "");

interface Props {
  rows: Txn[];
  categories: Category[];
  showAccount: boolean;
  sort: string;
  order: "asc" | "desc";
  onSort: (sort: string) => void;
  onEdit: (id: number, patch: TxnPatch) => void;
}

export function TransactionGrid({
  rows,
  categories,
  showAccount,
  sort,
  order,
  onSort,
  onEdit,
}: Props) {
  const columns = useMemo(
    () => [
      column.accessor("date", {
        header: "Date",
        meta: { sortKey: "date", className: "w-28 whitespace-nowrap" },
        cell: (cell) => <span className="px-1.5 text-ink-2">{dayLabel(cell.getValue())}</span>,
      }),
      column.accessor("payee", {
        header: "Payee",
        meta: { sortKey: "payee", className: "w-[20%]" },
        cell: ({ row }) => (
          <EditableText
            value={row.original.payee}
            label="Payee"
            placeholder="Add payee"
            onSave={(payee) => onEdit(row.original.id, { payee })}
          />
        ),
      }),
      column.accessor("category", {
        header: "Category",
        meta: { sortKey: "category", className: "w-[22%]" },
        cell: ({ row }) => (
          <EditableCategory
            categoryId={row.original.category_id}
            name={row.original.category}
            icon={row.original.category_icon}
            categories={categories}
            onSave={(category_id) => onEdit(row.original.id, { category_id })}
          />
        ),
      }),
      column.accessor("note", {
        header: "Note",
        meta: { className: "" },
        cell: ({ row }) => (
          <EditableText
            value={row.original.note}
            label="Note"
            placeholder="Add note"
            onSave={(note) => onEdit(row.original.id, { note })}
          />
        ),
      }),
      ...(showAccount
        ? [
            column.accessor("account", {
              header: "Account",
              meta: { sortKey: "account", className: "w-32" },
              cell: (cell) => <span className="px-1.5 text-ink-2">{cell.getValue()}</span>,
            }),
          ]
        : []),
      column.accessor("money_out", {
        header: "Out",
        meta: { sortKey: "money_out", className: "w-28 text-right" },
        cell: (cell) => money(cell.getValue()),
      }),
      column.accessor("money_in", {
        header: "In",
        meta: { sortKey: "money_in", className: "w-28 text-right" },
        cell: (cell) => money(cell.getValue()),
      }),
      column.accessor("balance", {
        header: "Balance",
        meta: { className: "w-32 text-right" },
        cell: (cell) => <span className="text-muted">{inrExact(cell.getValue())}</span>,
      }),
    ],
    [categories, showAccount, onEdit],
  );

  // Sorting, filtering and paging all happen on the server; the table only renders.
  const table = useReactTable({ data: rows, columns, getCoreRowModel: getCoreRowModel() });

  return (
    <div className="overflow-x-auto rounded-xl border border-line bg-surface">
      <table className="w-full min-w-[900px] table-fixed text-sm tabular-nums">
        <thead className="border-b border-line text-xs text-muted">
          <tr>
            {table.getFlatHeaders().map((header) => {
              const meta = header.column.columnDef.meta as { sortKey?: string; className: string };
              const sorted = meta.sortKey === sort;
              return (
                <th
                  key={header.id}
                  className={`px-3.5 py-2 font-medium ${
                    meta.className.includes("text-right") ? "" : "text-left"
                  } ${meta.className}`}
                  aria-sort={sorted ? (order === "asc" ? "ascending" : "descending") : undefined}
                >
                  {meta.sortKey ? (
                    <button
                      className="hover:text-ink"
                      onClick={() => onSort(meta.sortKey as string)}
                    >
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      <span className="ml-1 inline-block w-2" aria-hidden>
                        {sorted ? (order === "asc" ? "↑" : "↓") : ""}
                      </span>
                    </button>
                  ) : (
                    flexRender(header.column.columnDef.header, header.getContext())
                  )}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr
              key={row.original.id}
              className={`border-b border-line last:border-0 ${rowTint(row.original)}`}
            >
              {row.getVisibleCells().map((cell) => {
                const meta = cell.column.columnDef.meta as { className: string };
                return (
                  <td
                    key={cell.id}
                    className={`py-1 ${
                      meta.className.includes("text-right") ? "px-3.5" : "px-2"
                    } ${meta.className}`}
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length === 0 && (
        <p className="py-10 text-center text-sm text-muted">No transactions match these filters.</p>
      )}
    </div>
  );
}

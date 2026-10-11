import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";

import { api } from "../../api/client";
import { useAccounts, useApiQuery, useCategories } from "../../api/hooks";
import type { Txn, TxnPage, TxnPatch } from "../../api/types";
import { inr } from "../../lib/format";
import { useFilters } from "../../lib/useFilters";
import { TransactionFilters } from "./TransactionFilters";
import { TransactionGrid } from "./TransactionGrid";

const PAGE_SIZE = 50;
// Text columns read best A-Z first; dates and amounts newest/largest first.
const ASCENDING_FIRST = new Set(["payee", "category", "account"]);

export function TransactionsPage() {
  const { search, apiParams, update } = useFilters();
  const queryClient = useQueryClient();
  const categories = useCategories();
  const accounts = useAccounts();

  const sort = search.get("sort") ?? "date";
  const order = search.get("order") === "asc" ? "asc" : "desc";
  const page = Math.max(1, Number(search.get("page")) || 1);

  const transactions = useApiQuery<TxnPage>("/transactions", {
    ...apiParams,
    q: search.get("q"),
    category: search.get("category"),
    dir: search.get("dir"),
    min: search.get("min"),
    max: search.get("max"),
    unlabelled: search.get("unlabelled") === "true",
    sort,
    order,
    page,
    page_size: PAGE_SIZE,
  });

  const edit = useMutation({
    mutationFn: ({ id, patch }: { id: number; patch: TxnPatch }) =>
      api<Txn>(`/transactions/${id}`, { method: "PATCH", body: patch }),
    // An edit can move numbers on every page, so everything is refreshed.
    onSuccess: () => queryClient.invalidateQueries(),
  });
  const { mutate } = edit;
  const onEdit = useCallback((id: number, patch: TxnPatch) => mutate({ id, patch }), [mutate]);

  const onSort = (key: string) => {
    const nextOrder =
      key === sort ? (order === "asc" ? "desc" : "asc") : ASCENDING_FIRST.has(key) ? "asc" : "desc";
    update({ sort: key === "date" ? null : key, order: nextOrder === "desc" ? null : "asc" });
  };

  const data = transactions.data;
  const pages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div className="space-y-3">
      <TransactionFilters search={search} categories={categories.data ?? []} update={update} />

      <div className="flex min-h-5 flex-wrap items-baseline gap-x-4 text-sm text-muted">
        {data && (
          <>
            <span>
              <span className="font-medium text-ink">{data.total.toLocaleString("en-IN")}</span>{" "}
              transactions
            </span>
            <span>
              In <span className="font-medium text-ink">{inr(data.sum_in)}</span>
            </span>
            <span>
              Out <span className="font-medium text-ink">{inr(data.sum_out)}</span>
            </span>
          </>
        )}
        {edit.isError && (
          <span role="alert" className="text-rose-600 dark:text-rose-400">
            Could not save: {edit.error.message}
          </span>
        )}
      </div>

      {transactions.isError ? (
        <p className="py-10 text-center text-sm text-muted">{transactions.error.message}</p>
      ) : !data ? (
        <div className="h-96 animate-pulse rounded-xl bg-line/60" />
      ) : (
        <div className={transactions.isPlaceholderData ? "opacity-50 transition-opacity" : ""}>
          <TransactionGrid
            rows={data.items}
            categories={categories.data ?? []}
            showAccount={(accounts.data?.length ?? 0) > 1}
            sort={sort}
            order={order}
            onSort={onSort}
            onEdit={onEdit}
          />
        </div>
      )}

      {data && data.total > PAGE_SIZE && (
        <div className="flex items-center justify-end gap-2 text-sm">
          <span className="mr-2 text-muted">
            Page {page} of {pages}
          </span>
          <button className="btn" disabled={page <= 1} onClick={() => update({ page: page - 1 })}>
            Previous
          </button>
          <button
            className="btn"
            disabled={page >= pages}
            onClick={() => update({ page: page + 1 })}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

import { useEffect, useState, type InputHTMLAttributes } from "react";

import type { Category } from "../../api/types";
import type { FilterPatch } from "../../lib/useFilters";
import { CategoryOptions } from "./EditableCell";

const PAGE_KEYS = ["q", "category", "dir", "min", "max", "unlabelled"] as const;

/** A text box that writes to the URL a moment after typing stops. */
function DebouncedInput({
  value,
  onCommit,
  ...props
}: {
  value: string;
  onCommit: (value: string) => void;
} & Omit<InputHTMLAttributes<HTMLInputElement>, "value" | "onChange">) {
  const [draft, setDraft] = useState(value);
  useEffect(() => setDraft(value), [value]);
  useEffect(() => {
    if (draft === value) return;
    const timer = setTimeout(() => onCommit(draft), 300);
    return () => clearTimeout(timer);
  }, [draft, value, onCommit]);
  return <input {...props} value={draft} onChange={(event) => setDraft(event.target.value)} />;
}

interface Props {
  search: URLSearchParams;
  categories: Category[];
  update: (patch: FilterPatch) => void;
}

export function TransactionFilters({ search, categories, update }: Props) {
  const get = (key: string) => search.get(key) ?? "";
  const active = PAGE_KEYS.some((key) => search.has(key));

  return (
    <div className="flex flex-wrap items-center gap-2">
      <DebouncedInput
        type="search"
        aria-label="Search payee or note"
        placeholder="Search payee or note"
        className="field w-56"
        value={get("q")}
        onCommit={(q) => update({ q })}
      />
      <select
        aria-label="Category"
        className="field max-w-[15rem]"
        value={get("category")}
        onChange={(event) => update({ category: event.target.value })}
      >
        <option value="">All categories</option>
        <CategoryOptions categories={categories} />
      </select>
      <select
        aria-label="Direction"
        className="field"
        value={get("dir")}
        onChange={(event) => update({ dir: event.target.value })}
      >
        <option value="">In and out</option>
        <option value="in">Money in</option>
        <option value="out">Money out</option>
      </select>
      <DebouncedInput
        type="number"
        min={0}
        aria-label="Minimum amount"
        placeholder="Min ₹"
        className="field w-24"
        value={get("min")}
        onCommit={(min) => update({ min })}
      />
      <DebouncedInput
        type="number"
        min={0}
        aria-label="Maximum amount"
        placeholder="Max ₹"
        className="field w-24"
        value={get("max")}
        onCommit={(max) => update({ max })}
      />
      <label className="flex h-9 cursor-pointer items-center gap-2 rounded-md border border-line bg-surface px-2.5 text-sm">
        <input
          type="checkbox"
          checked={search.get("unlabelled") === "true"}
          onChange={(event) => update({ unlabelled: event.target.checked })}
        />
        Unlabelled only
      </label>
      {active && (
        <button
          className="btn"
          onClick={() => update(Object.fromEntries(PAGE_KEYS.map((key) => [key, null])))}
        >
          Clear
        </button>
      )}
    </div>
  );
}

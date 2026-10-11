import { useRef, useState, type KeyboardEvent } from "react";

import type { Category } from "../../api/types";

const CELL_BUTTON =
  "block w-full truncate rounded px-1.5 py-1 text-left hover:bg-ink/5 focus-visible:outline focus-visible:outline-1 focus-visible:outline-sky-500";

/** Click to edit; Enter or leaving the field saves, Escape cancels. */
export function EditableText({
  value,
  placeholder,
  label,
  onSave,
}: {
  value: string;
  placeholder: string;
  label: string;
  onSave: (next: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  const cancelled = useRef(false);

  if (!editing) {
    return (
      <button
        className={CELL_BUTTON}
        title={value || undefined}
        aria-label={`${label}: ${value || "empty"}. Click to edit`}
        onClick={() => {
          setDraft(value);
          cancelled.current = false;
          setEditing(true);
        }}
      >
        {value || <span className="text-muted/60">{placeholder}</span>}
      </button>
    );
  }

  const finish = () => {
    setEditing(false);
    const next = draft.trim();
    if (!cancelled.current && next !== value) onSave(next);
  };
  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") event.currentTarget.blur();
    if (event.key === "Escape") {
      cancelled.current = true;
      event.currentTarget.blur();
    }
  };

  return (
    <input
      autoFocus
      aria-label={label}
      value={draft}
      onChange={(event) => setDraft(event.target.value)}
      onBlur={finish}
      onKeyDown={onKeyDown}
      className="w-full rounded border border-sky-500 bg-surface px-1.5 py-1 outline-none"
    />
  );
}

export function CategoryOptions({ categories }: { categories: Category[] }) {
  const groups = new Map<string, Category[]>();
  for (const category of categories) {
    groups.set(category.group.name, [...(groups.get(category.group.name) ?? []), category]);
  }
  return (
    <>
      {[...groups].map(([group, members]) => (
        <optgroup key={group} label={group}>
          {members.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </optgroup>
      ))}
    </>
  );
}

export function EditableCategory({
  categoryId,
  name,
  icon,
  categories,
  onSave,
}: {
  categoryId: number;
  name: string;
  icon: string | null;
  categories: Category[];
  onSave: (categoryId: number) => void;
}) {
  const [editing, setEditing] = useState(false);

  if (!editing) {
    return (
      <button
        className={CELL_BUTTON}
        title={name}
        aria-label={`Category: ${name}. Click to change`}
        onClick={() => setEditing(true)}
      >
        <span className="mr-1.5 inline-block w-5 text-center" aria-hidden>
          {icon}
        </span>
        {name}
      </button>
    );
  }
  return (
    <select
      autoFocus
      aria-label="Category"
      value={categoryId}
      onBlur={() => setEditing(false)}
      onKeyDown={(event) => event.key === "Escape" && setEditing(false)}
      onChange={(event) => {
        setEditing(false);
        onSave(Number(event.target.value));
      }}
      className="w-full rounded border border-sky-500 bg-surface px-1 py-1 outline-none"
    >
      <CategoryOptions categories={categories} />
    </select>
  );
}

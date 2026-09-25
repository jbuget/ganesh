"use client";

import { Plus, X } from "lucide-react";
import { useState } from "react";

interface TagListFieldProps {
  values: string[];
  /** What the row asks for: the empty state and the accessible name. */
  label: string;
  placeholder: string;
  /**
   * Whether the reader may change it.
   *
   * Editable by default: a field one cannot change is the exception, and it
   * is the screen holding the field that knows — a guest reads every sheet of
   * the reference list and rewrites none.
   */
  editable?: boolean;
  onChange: (values: string[]) => void | Promise<void>;
}

/**
 * A list of short words, added one at a time and removed by the cross.
 *
 * The whole list is sent on every change: the server replaces what it holds
 * with what the screen shows, so there is no adding one and removing another.
 *
 * Typing one entry after another is faster than the round trip that saves
 * them. The field therefore keeps what it has just added on its own, and adds
 * to that rather than to the prop: without it, the second entry would be sent
 * alongside a list that does not know about the first, and the first would be
 * lost. What the server sends back takes over as soon as it names the same
 * entries.
 */
export function TagListField({
  values,
  label,
  placeholder,
  editable = true,
  onChange,
}: TagListFieldProps) {
  const [entry, setEntry] = useState<string | null>(null);
  const [added, setAdded] = useState<string[]>([]);

  // Entries the server has not confirmed yet, in the order they were typed.
  const pending = added.filter((value) => !values.includes(value));
  const shown = [...values, ...pending];

  function add() {
    if (entry === null) return;
    const typed = entry.trim();
    setEntry(null);
    if (!typed || shown.includes(typed)) return;
    setAdded([...added, typed]);
    void onChange([...shown, typed]);
  }

  function remove(value: string) {
    setAdded(added.filter((kept) => kept !== value));
    void onChange(shown.filter((kept) => kept !== value));
  }

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {shown.map((value) => (
        <span
          key={value}
          className="flex items-center gap-1 rounded border border-slate-200 bg-white py-0.5 pr-1 pl-2 text-sm text-slate-700"
        >
          {value}
          {editable && (
            <button
              type="button"
              aria-label={`Retirer ${value}`}
              onClick={() => remove(value)}
              className="cursor-pointer rounded p-0.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
            >
              <X className="size-3" aria-hidden />
            </button>
          )}
        </span>
      ))}

      {entry !== null ? (
        <input
          type="text"
          autoFocus
          value={entry}
          aria-label={label}
          placeholder={placeholder}
          onChange={(event) => setEntry(event.target.value)}
          onBlur={add}
          onKeyDown={(event) => {
            // Enter keeps the field open: a list is typed in one go.
            if (event.key === "Enter") {
              add();
              setEntry("");
            }
            if (event.key === "Escape") {
              // Cancelling a field cancels the field, not the visit: without
              // this the panel behind would close on the same key.
              event.stopPropagation();
              setEntry(null);
            }
          }}
          className="w-40 rounded border border-slate-400 px-1.5 py-0.5 text-sm focus:outline-none"
        />
      ) : (
        <button
          type="button"
          aria-label={label}
          onClick={() => setEntry("")}
          className="flex cursor-pointer items-center gap-1 rounded px-1 py-0.5 text-sm text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
        >
          <Plus className="size-3.5" aria-hidden />
          {shown.length === 0 ? label : "Ajouter"}
        </button>
      )}
    </div>
  );
}

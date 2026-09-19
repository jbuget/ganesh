"use client";

import { Plus } from "lucide-react";
import { useState } from "react";

interface InlineTextFieldProps {
  value: string | null | undefined;
  /** What the row asks for, shown as the empty state and read by assistive tech. */
  label: string;
  placeholder?: string;
  /** Offered while the field is empty, one click away from being accepted. */
  suggestion?: string | null;
  /**
   * Whether the reader may write.
   *
   * Editable by default: a field one cannot change is the exception, and a
   * screen that only reads says so on its own.
   */
  editable?: boolean;
  onChange: (value: string | null) => void | Promise<void>;
}

/**
 * A line of text that edits where it shows.
 *
 * The field only appears on click: a sheet is read far more often than it is
 * changed, and a permanent input border would make noise on every row.
 */
export function InlineTextField({
  value,
  label,
  placeholder,
  suggestion,
  editable = true,
  onChange,
}: InlineTextFieldProps) {
  const [entry, setEntry] = useState<string | null>(null);

  function validate() {
    if (entry === null) return;
    const trimmed = entry.trim();
    setEntry(null);
    const next = trimmed === "" ? null : trimmed;
    if (next !== (value ?? null)) void onChange(next);
  }

  if (!editable) {
    return value ? (
      <span className="text-sm text-slate-700">{value}</span>
    ) : (
      <span className="text-sm text-slate-400">Non renseigné</span>
    );
  }

  if (entry !== null) {
    return (
      <input
        type="text"
        autoFocus
        value={entry}
        aria-label={label}
        placeholder={placeholder}
        onChange={(event) => setEntry(event.target.value)}
        onBlur={validate}
        onKeyDown={(event) => {
          if (event.key === "Enter") validate();
          if (event.key === "Escape") {
            // Cancelling a field cancels the field, not the visit: without this
            // the panel behind would close on the same key.
            event.stopPropagation();
            setEntry(null);
          }
        }}
        className="w-full rounded border border-slate-400 px-1.5 py-0.5 text-sm focus:outline-none"
      />
    );
  }

  return (
    <div className="flex min-w-0 items-center gap-2">
      <button
        type="button"
        aria-label={label}
        onClick={() => setEntry(value ?? "")}
        className="-mx-1 min-w-0 cursor-pointer rounded px-1 py-0.5 text-left text-sm transition-colors hover:bg-slate-100"
      >
        {value ? (
          <span className="block truncate text-slate-700">{value}</span>
        ) : (
          <span className="flex items-center gap-1 text-slate-400">
            <Plus className="size-3.5" aria-hidden />
            {label}
          </span>
        )}
      </button>

      {/* Only while empty: once something is typed, a suggestion would be an
          invitation to undo it. */}
      {!value && suggestion && (
        <button
          type="button"
          onClick={() => void onChange(suggestion)}
          className="shrink-0 cursor-pointer text-xs text-slate-400 underline-offset-2 transition-colors hover:text-slate-700 hover:underline"
        >
          {suggestion}
        </button>
      )}
    </div>
  );
}

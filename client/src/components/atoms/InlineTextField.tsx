"use client";

import { Plus } from "lucide-react";
import { useState } from "react";

interface InlineTextFieldProps {
  value: string | null | undefined;
  /** What the field holds: read as a prompt while it is empty. */
  label: string;
  /** Without the right to write, the field reads and no more. */
  editable: boolean;
  onChange: (value: string | null) => void | Promise<void>;
}

/**
 * A line of text that edits where it shows.
 *
 * Same reasoning as the number field: a sheet is read far more often than it
 * is written, and a permanent input border would make noise on every row.
 */
export function InlineTextField({
  value,
  label,
  editable,
  onChange,
}: InlineTextFieldProps) {
  const [entry, setEntry] = useState<string | null>(null);
  const current = value ?? null;

  function validate() {
    if (entry === null) return;
    const trimmed = entry.trim();
    setEntry(null);
    const next = trimmed === "" ? null : trimmed;
    if (next !== current) void onChange(next);
  }

  if (!editable) {
    return current ? (
      <span className="text-sm text-slate-700">{current}</span>
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
        onChange={(event) => setEntry(event.target.value)}
        onBlur={validate}
        onKeyDown={(event) => {
          if (event.key === "Enter") validate();
          // Stops at the field: the panel closes on Escape too, and giving up
          // on a word must not carry the whole screen away with it.
          if (event.key === "Escape") {
            event.stopPropagation();
            setEntry(null);
          }
        }}
        className="w-56 rounded border border-slate-400 px-1.5 py-0.5 text-sm focus:outline-none"
      />
    );
  }

  return (
    <button
      type="button"
      aria-label={label}
      onClick={() => setEntry(current ?? "")}
      className="-mx-1 cursor-pointer rounded px-1 py-0.5 text-sm transition-colors hover:bg-slate-100"
    >
      {current ? (
        <span className="text-slate-700">{current}</span>
      ) : (
        <span className="flex items-center gap-1 text-slate-400">
          <Plus className="size-3.5" aria-hidden />
          {label}
        </span>
      )}
    </button>
  );
}

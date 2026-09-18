"use client";

import { Plus } from "lucide-react";
import { useState } from "react";

interface InlineNumberFieldProps {
  value: number | null | undefined;
  suffixe: string;
  invite: string;
  onChange: (value: number | null) => void | Promise<void>;
}

/**
 * A number that edits where it shows.
 *
 * The field only appears on click: a sheet is read far more often than it is
 * changed, and a permanent input border would make noise on every row.
 */
export function InlineNumberField({
  value,
  suffixe,
  invite,
  onChange,
}: InlineNumberFieldProps) {
  const [entry, setSaisie] = useState<string | null>(null);

  function validate() {
    if (entry === null) return;
    const propre = entry.trim().replace(",", ".");
    setSaisie(null);
    const count = propre === "" ? null : Number(propre);
    if (count !== null && (Number.isNaN(count) || count < 0)) return;
    if (count !== (value ?? null)) void onChange(count);
  }

  if (entry !== null) {
    return (
      <input
        type="text"
        inputMode="decimal"
        autoFocus
        value={entry}
        aria-label={invite}
        onChange={(event) => setSaisie(event.target.value)}
        onBlur={validate}
        onKeyDown={(event) => {
          if (event.key === "Enter") validate();
          if (event.key === "Escape") setSaisie(null);
        }}
        className="w-24 rounded border border-slate-400 px-1.5 py-0.5 text-sm focus:outline-none"
      />
    );
  }

  return (
    <button
      type="button"
      aria-label={invite}
      onClick={() =>
        setSaisie(value === null || value === undefined ? "" : String(value))
      }
      className="-mx-1 cursor-pointer rounded px-1 py-0.5 text-sm transition-colors hover:bg-slate-100"
    >
      {value === null || value === undefined ? (
        <span className="flex items-center gap-1 text-slate-400">
          <Plus className="size-3.5" aria-hidden />
          {invite}
        </span>
      ) : (
        <span className="text-slate-700">
          {value} {suffixe}
        </span>
      )}
    </button>
  );
}

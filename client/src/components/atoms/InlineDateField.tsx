"use client";

import { CalendarPlus, X } from "lucide-react";
import { useState } from "react";

import { formatSpelledDate } from "@/lib/dates";

interface InlineDateFieldProps {
  value: string | null;
  /** What the field is for, read out to whoever cannot see the row. */
  label: string;
  /**
   * Whether the reader may change it.
   *
   * Editable by default: a field one cannot change is the exception, and the
   * screen holding it is what knows.
   */
  editable?: boolean;
  /**
   * Whether emptying it is offered.
   *
   * Off by default: a date a row cannot do without — a milestone's announced
   * day — must not be shown a cross that would leave the line saying nothing.
   */
  clearable?: boolean;
  /** Whether the day has gone by without what it announced happening. */
  late?: boolean;
  onChange: (value: string | null) => void | Promise<void>;
}

/**
 * A date that edits where it shows.
 *
 * `TargetDateField` is the same gesture for one particular date — the day a
 * mission is announced for — and carries that date's own reading of lateness,
 * which follows the phase. This one is told whether it is late rather than
 * working it out: a milestone is excused by having happened, not by a phase,
 * and a field that reasoned about both would answer neither question well.
 */
export function InlineDateField({
  value,
  label,
  editable = true,
  clearable = false,
  late = false,
  onChange,
}: InlineDateFieldProps) {
  const [entry, setEntry] = useState<string | null>(null);

  function commit(next: string) {
    setEntry(null);
    const chosen = next.trim() === "" ? null : next;
    if (chosen !== value) void onChange(chosen);
  }

  if (!editable) {
    return value ? (
      <span
        className={`text-sm tabular-nums ${late ? "font-medium text-red-600" : "text-slate-600"}`}
      >
        {formatSpelledDate(value)}
      </span>
    ) : (
      <span className="text-sm text-slate-400">—</span>
    );
  }

  if (entry !== null) {
    return (
      <input
        type="date"
        autoFocus
        value={entry}
        aria-label={label}
        onChange={(event) => setEntry(event.target.value)}
        onBlur={(event) => commit(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter") commit(event.currentTarget.value);
          if (event.key === "Escape") {
            // Cancelling a field cancels the field, not the visit: without
            // this the panel behind would close on the same key.
            event.stopPropagation();
            setEntry(null);
          }
        }}
        className="w-32 cursor-pointer rounded border border-slate-400 px-1 py-0.5 text-sm focus:outline-none"
      />
    );
  }

  return (
    <span className="flex items-center gap-0.5">
      <button
        type="button"
        aria-label={label}
        onClick={() => setEntry(value ?? "")}
        className="-mx-1 cursor-pointer rounded px-1 py-0.5 text-sm whitespace-nowrap transition-colors hover:bg-slate-100"
      >
        {value ? (
          <span
            className={
              late
                ? "font-medium text-red-600 tabular-nums"
                : "text-slate-600 tabular-nums"
            }
          >
            {formatSpelledDate(value)}
          </span>
        ) : (
          <span className="flex items-center gap-1 text-slate-400">
            <CalendarPlus className="size-3.5" aria-hidden />
            Dater
          </span>
        )}
      </button>

      {/* Said in words as well as in colour: a reader who cannot tell red from
          grey would otherwise be told nothing at all. */}
      {late && (
        <span className="ml-1.5 text-xs whitespace-nowrap text-red-600">en retard</span>
      )}

      {value && clearable && (
        <button
          type="button"
          aria-label={`Retirer ${label}`}
          onClick={() => void onChange(null)}
          className="cursor-pointer rounded p-0.5 text-slate-300 transition-colors hover:text-slate-500"
        >
          <X className="size-3" aria-hidden />
        </button>
      )}
    </span>
  );
}

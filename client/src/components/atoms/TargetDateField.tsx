"use client";

import { CalendarPlus, X } from "lucide-react";
import { useState } from "react";

import { formatSpelledDate } from "@/lib/dates";

interface TargetDateFieldProps {
  value: string | null;
  /** What the field is for, read out to whoever cannot see the row. */
  missionLabel: string;
  onChange: (value: string | null) => void | Promise<void>;
  /**
   * Whether the reader may post a date.
   *
   * Editable by default: a field one cannot change is the exception, and it
   * is the screen holding the field that knows.
   */
  editable?: boolean;
  /**
   * Set in a table, where a row holds a dozen figures and the date is one
   * of them. A sheet reads its values at the size of its other values.
   */
  dense?: boolean;
}

/**
 * The date a mission is announced for, posted where it is read.
 *
 * Read and written in two places, and the same field in both: on the roadmap,
 * where a commitment is taken against every other date rather than in
 * isolation, and on the mission's own sheet, where one is already changing
 * its phase and its priority.
 *
 * Every change is traced — the reference list records it — which is what
 * eventually makes « annoncée trois fois » a thing one can read.
 */
export function TargetDateField({
  value,
  missionLabel,
  onChange,
  editable = true,
  dense = false,
}: TargetDateFieldProps) {
  const [entry, setEntry] = useState<string | null>(null);
  const size = dense ? "text-xs" : "text-sm";

  function validate(next: string) {
    setEntry(null);
    const chosen = next.trim() === "" ? null : next;
    if (chosen !== value) void onChange(chosen);
  }

  if (entry !== null) {
    return (
      <input
        type="date"
        autoFocus
        value={entry}
        aria-label={`Date annoncée pour ${missionLabel}`}
        onChange={(event) => setEntry(event.target.value)}
        onBlur={(event) => validate(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter") validate(event.currentTarget.value);
          if (event.key === "Escape") {
            event.stopPropagation();
            setEntry(null);
          }
        }}
        className={`w-36 cursor-pointer rounded border border-slate-400 px-1 py-0.5 ${size} focus:outline-none`}
      />
    );
  }

  return (
    <span className="flex items-center gap-0.5">
      <button
        type="button"
        aria-label={`Date annoncée pour ${missionLabel}`}
        disabled={!editable}
        onClick={() => setEntry(value ?? "")}
        className={`-mx-1 rounded px-1 py-0.5 ${size} whitespace-nowrap transition-colors ${
          editable ? "cursor-pointer hover:bg-slate-100" : ""
        }`}
      >
        {value ? (
          <span className="text-slate-600 tabular-nums">
            {formatSpelledDate(value)}
          </span>
        ) : (
          <span className="flex items-center gap-1 text-slate-400">
            <CalendarPlus className="size-3.5" aria-hidden />
            Dater
          </span>
        )}
      </button>

      {value && editable && (
        <button
          type="button"
          aria-label={`Retirer la date annoncée pour ${missionLabel}`}
          onClick={() => void onChange(null)}
          className="cursor-pointer rounded p-0.5 text-slate-300 transition-colors hover:text-slate-500"
        >
          <X className="size-3" aria-hidden />
        </button>
      )}
    </span>
  );
}

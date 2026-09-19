"use client";

import { CalendarPlus, X } from "lucide-react";
import { useState } from "react";

import { formatSpelledDate } from "@/lib/dates";

interface TargetDateFieldProps {
  value: string | null;
  /** What the field is for, read out to whoever cannot see the row. */
  missionLabel: string;
  onChange: (value: string | null) => void | Promise<void>;
}

/**
 * The date a mission is announced for, posted where it is read.
 *
 * The one thing this screen writes. Posting a date while looking at every
 * other date is the whole reason it belongs here rather than on a form: a
 * commitment is taken against the others, not in isolation.
 *
 * Every change is traced — the reference list records it — which is what
 * eventually makes « annoncée trois fois » a thing one can read.
 */
export function TargetDateField({
  value,
  missionLabel,
  onChange,
}: TargetDateFieldProps) {
  const [entry, setEntry] = useState<string | null>(null);

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
        className="w-32 cursor-pointer rounded border border-slate-400 px-1 py-0.5 text-xs focus:outline-none"
      />
    );
  }

  return (
    <span className="flex items-center gap-0.5">
      <button
        type="button"
        aria-label={`Date annoncée pour ${missionLabel}`}
        onClick={() => setEntry(value ?? "")}
        className="-mx-1 cursor-pointer rounded px-1 py-0.5 text-xs whitespace-nowrap transition-colors hover:bg-slate-100"
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

      {value && (
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

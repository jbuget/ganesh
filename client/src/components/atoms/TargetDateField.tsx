"use client";

import { CalendarPlus, X } from "lucide-react";
import { useState } from "react";

import type { ProjectStatus } from "@/lib/api/generated/model";
import { formatSpelledDate } from "@/lib/dates";
import { isGoLiveLate } from "@/lib/go-live";

interface TargetDateFieldProps {
  value: string | null;
  /** What the field is for, read out to whoever cannot see the row. */
  missionLabel: string;
  /**
   * Where the mission stands, and the day to read it against.
   *
   * Given together or not at all. A screen that already draws lateness of its
   * own — the roadmap does, with its red thread — passes neither, and the
   * field says nothing the drawing beside it is about to say again.
   */
  status?: ProjectStatus | null;
  today?: Date;
  /**
   * Whether the reader may change it.
   *
   * Editable by default: a field one cannot change is the exception, and it
   * is the screen holding the field that knows — a guest reads every sheet of
   * the reference list and rewrites none.
   */
  editable?: boolean;
  onChange: (value: string | null) => void | Promise<void>;
}

/**
 * The date a mission is announced for, posted where it is read.
 *
 * Two screens post it: the roadmap, where a commitment is taken against every
 * other date rather than in isolation, and the sheet of a project, where one
 * arrives already looking at that project. One field for both — the gesture
 * is the same one, and two of them would drift apart within a month.
 *
 * It takes its size from where it is put: a dense column of dates is read at
 * a glance, a single line of a sheet is read beside its neighbours.
 *
 * Every change is traced — the reference list records it — which is what
 * eventually makes « annoncée trois fois » a thing one can read.
 */
export function TargetDateField({
  value,
  missionLabel,
  status,
  today,
  editable = true,
  onChange,
}: TargetDateFieldProps) {
  const [entry, setEntry] = useState<string | null>(null);
  const isLate = today !== undefined && isGoLiveLate(value, status, today);

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
        className="w-32 cursor-pointer rounded border border-slate-400 px-1 py-0.5 focus:outline-none"
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
        className={`-mx-1 rounded px-1 py-0.5 whitespace-nowrap transition-colors ${
          editable ? "cursor-pointer hover:bg-slate-100" : ""
        }`}
      >
        {value ? (
          <span
            className={
              isLate
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

      {/* Said in words as well as in colour: a reader who cannot tell red
          from grey would otherwise be told nothing at all. Spaced by `ml-1.5`
          rather than by the row's gap, which the button's `-mx-1` eats. */}
      {isLate && (
        <span className="ml-1.5 text-xs whitespace-nowrap text-red-600">en retard</span>
      )}

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

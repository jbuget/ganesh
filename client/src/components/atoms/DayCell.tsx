"use client";

import { cycleDayValue, type DayValue } from "@/lib/day-value";
import { formatDays } from "@/lib/dates";

interface DayCellProps {
  value: DayValue;
  isOffDay: boolean;
  isFuture: boolean;
  isReadOnly: boolean;
  /** The last row closes the table: its bottom rule is the strong one. */
  isLastRow?: boolean;
  /** The last day column carries the rule that separates it from the totals. */
  isLastDay?: boolean;
  /** A non-working day shrinks to a band, unless it carries an entry. */
  isNarrow?: boolean;
  label: string;
  onChange: (next: DayValue) => void;
}

/**
 * A single cell of the grid.
 *
 * Borders are carried by the `<td>`, never by the button: the button would draw
 * over the rule.
 *
 * Non-working days are greyed and locked, future days dimmed: the first to
 * avoid entries by mistake, the second because they are forecast and not
 * delivered. Today is marked only in the column header, so as not to clutter
 * the grid.
 */
export function DayCell({
  value,
  isOffDay,
  isFuture,
  isReadOnly,
  isLastRow = false,
  isLastDay = false,
  isNarrow = false,
  label,
  onChange,
}: DayCellProps) {
  // A non-working day is never entered on. The rule is carried by the domain,
  // locking the cell is only its reflection.
  const isLocked = isReadOnly || isOffDay;

  const background =
    value > 0
      ? "bg-sky-100 font-medium text-sky-900"
      : isOffDay
        ? "bg-slate-100"
        : "bg-white";

  return (
    <td
      className={[
        "border-r border-b p-0",
        isLastDay ? "border-r-slate-500" : "border-r-slate-300",
        isLastRow ? "border-b-slate-500" : "border-b-slate-300",
      ].join(" ")}
    >
      <button
        type="button"
        aria-label={label}
        title={label}
        disabled={isLocked}
        onClick={() => onChange(cycleDayValue(value))}
        className={[
          "block h-9 text-sm transition-colors",
          isNarrow ? "w-2.5" : "w-9",
          background,
          isFuture && value > 0 ? "opacity-60" : "",
          isLocked ? "cursor-not-allowed" : "cursor-pointer hover:bg-sky-50",
        ].join(" ")}
      >
        {formatDays(value)}
      </button>
    </td>
  );
}

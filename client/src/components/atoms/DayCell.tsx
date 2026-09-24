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
  /**
   * How the grid names this cell, so the keys can find it back. The handler
   * lives on the table: the cell only has to say which one it is.
   */
  cellId: string;
  /**
   * Whether this cell is the grid's one stop in the tab order. A grid holds a
   * single one, which follows the focus — tabbing through three hundred cells
   * to reach what comes after them is not navigation.
   */
  isTabStop?: boolean;
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
  cellId,
  isTabStop = false,
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
        data-cell={cellId}
        tabIndex={isTabStop ? 0 : -1}
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

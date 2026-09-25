"use client";

import { formatHours, type DayValue } from "@/lib/day-value";

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
}

/**
 * A single cell of the grid.
 *
 * **The cell is the control.** There is no button inside it, because there is
 * nothing here to press: a value is typed, not clicked. A click lands the
 * focus and stops there — it used to cycle the value, which meant putting an
 * 8 in every cell one clicked in order to type in it.
 *
 * That also settles what the cell is to a screen reader. A button that does
 * nothing when pressed is a lie; a `gridcell` says what this is, and the
 * arrows say how to move between them. `role="grid"` is carried by the table.
 *
 * Non-working days are greyed and left out of the tab order entirely, future
 * days dimmed: the first so nothing can be entered on them, the second because
 * they are forecast and not delivered. A locked cell takes no focus, so no key
 * ever reaches it and there is nothing to refuse. Today is marked only in the
 * column header, so as not to clutter the grid.
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
      // Spelled out rather than left to the `role="grid"` above: browsers and
      // tooling do not all derive it the same way, and this is the one role
      // that says the cell can be walked into and written in.
      role="gridcell"
      data-cell={cellId}
      // No `tabIndex` at all when locked: absent is what keeps the cell out of
      // the tab order, where -1 would still let a script focus it.
      tabIndex={isLocked ? undefined : isTabStop ? 0 : -1}
      aria-label={label}
      aria-readonly={isLocked || undefined}
      title={label}
      className={[
        "h-9 border-r border-b text-center text-sm transition-colors",
        isNarrow ? "w-2.5" : "w-9",
        isLastDay ? "border-r-slate-500" : "border-r-slate-300",
        isLastRow ? "border-b-slate-500" : "border-b-slate-300",
        background,
        isFuture && value > 0 ? "opacity-60" : "",
        isLocked ? "cursor-not-allowed" : "cursor-pointer hover:bg-sky-50",
      ].join(" ")}
    >
      {formatHours(value)}
    </td>
  );
}

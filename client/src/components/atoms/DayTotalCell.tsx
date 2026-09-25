import type { StrongSide } from "@/lib/table-frame";
import { formatHours } from "@/lib/day-value";

interface DayTotalCellProps {
  value: number;
  isOffDay: boolean;
  /** A non-working day shrinks to a band, unless it carries an entry. */
  isNarrow?: boolean;
  strongSides?: StrongSide[];
}

/**
 * A day's total, across every mission.
 *
 * The background carries the state of the day: green when it is complete, red
 * when it is not — whether time is missing or there is too much. That is the
 * useful daily reading: spotting at a glance the days to fix.
 *
 * Read in hours, like the cells it adds up: a « 8 » under a column of hours
 * is the sum one checks at a glance, where « 1 » would have to be converted
 * back before it said anything.
 */
function backgroundFor(value: number, isOffDay: boolean) {
  if (value > 0) {
    return value === 1 ? "bg-emerald-100 text-emerald-900" : "bg-red-100 text-red-800";
  }
  if (isOffDay) return "bg-slate-100 text-slate-500";
  return "bg-white";
}

export function DayTotalCell({
  value,
  isOffDay,
  isNarrow = false,
  strongSides = [],
}: DayTotalCellProps) {
  const strong = new Set(strongSides);
  const isIncomplete = value > 0 && value !== 1;

  return (
    <td
      data-alert={isIncomplete ? "true" : undefined}
      className={[
        "h-9 border-r border-b text-center text-sm font-medium",
        isNarrow ? "w-2.5" : "w-9",
        strong.has("right") ? "border-r-slate-500" : "border-r-slate-300",
        strong.has("bottom") ? "border-b-slate-500" : "border-b-slate-300",
        backgroundFor(value, isOffDay),
      ].join(" ")}
    >
      {formatHours(value)}
    </td>
  );
}

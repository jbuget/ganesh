import { dayNumber, weekdayInitial } from "@/lib/dates";

interface DayHeaderProps {
  day: string;
  isOffDay: boolean;
  isToday: boolean;
  /** A non-working day shrinks to a band, unless it carries an entry. */
  isNarrow?: boolean;
  /** The last day column carries the rule that separates it from the totals. */
  isLastDay?: boolean;
  label: string | null;
}

/**
 * Header of a day column.
 *
 * Non-working days are greyed and shrunk to a band: nothing can be entered on
 * them, and giving them a full column cost a fifth of the table's width. The
 * rhythm of the weeks stays readable.
 */
export function DayHeader({
  day,
  isOffDay,
  isToday,
  isNarrow = false,
  isLastDay = false,
  label,
}: DayHeaderProps) {
  const heading = `${weekdayInitial(day)} ${dayNumber(day)}`;

  return (
    <th
      scope="col"
      title={label ?? heading}
      className={[
        "h-11 border-t border-r border-b border-t-slate-500 border-b-slate-300 text-xs font-normal",
        isNarrow ? "w-2.5" : "w-9",
        isLastDay ? "border-r-slate-500" : "border-r-slate-300",
        isOffDay
          ? "bg-slate-100 text-slate-500"
          : isToday
            ? "bg-amber-100 text-amber-900"
            : "bg-white text-slate-700",
        isToday ? "font-semibold" : "",
      ].join(" ")}
    >
      {isNarrow ? (
        // Shrunk to a band, the column keeps its heading for screen readers:
        // an anonymous column would make the table incomprehensible.
        <span className="sr-only">{heading}</span>
      ) : (
        <>
          <div className="leading-tight">{weekdayInitial(day)}</div>
          <div className="leading-tight">{dayNumber(day)}</div>
        </>
      )}
    </th>
  );
}

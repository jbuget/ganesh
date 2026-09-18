import { formatDecimalDays } from "@/lib/dates";

/** Side of a cell carrying a strong rule rather than the grid line. */
export type StrongSide = "right" | "bottom";

interface TotalCellProps {
  value: number;
  isAlert?: boolean;
  isStrong?: boolean;
  strongSides?: StrongSide[];
}

/**
 * A total cell, at the foot of a column or the end of a row.
 *
 * A total is written in decimal, \u00ab 14,5 \u00bb, where an entry cell keeps
 * \u00ab ½ \u00bb: the fraction does say a half day set on a day, but it reads
 * poorly as soon as it follows a number, and a running total compares by its
 * figure.
 *
 * The colour of each border is decided here, never by a class added from
 * outside: two competing colour classes on the same side would leave the
 * Tailwind sheet to arbitrate, which is not deterministic.
 */
export function TotalCell({
  value,
  isAlert,
  isStrong,
  strongSides = [],
}: TotalCellProps) {
  const strong = new Set(strongSides);

  return (
    <td
      data-alert={isAlert ? "true" : undefined}
      className={[
        "h-9 w-14 border-r border-b text-center text-sm",
        strong.has("right") ? "border-r-slate-500" : "border-r-slate-300",
        strong.has("bottom") ? "border-b-slate-500" : "border-b-slate-300",
        isAlert ? "bg-red-100 text-red-800 font-semibold" : "bg-slate-50",
        isStrong ? "font-semibold" : "",
      ].join(" ")}
    >
      {value === 0 ? "" : formatDecimalDays(value)}
    </td>
  );
}

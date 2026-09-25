import type { StrongSide } from "@/lib/table-frame";

interface CompletionCellProps {
  complete: number;
  workingDays: number;
  strongSides?: StrongSide[];
}

/**
 * How many days of the month are filled in, at the corner of the grid.
 *
 * It sits where a column of sums meets a row of sums, and it is not one: this
 * is a count, and it has to read as one or « 20 » will be taken for days
 * declared. Hence the ratio, which no total in the grid has ever carried, and
 * the ordinary weight — the totals around it are bold.
 *
 * Deliberately not coloured. A month in progress is not complete and that is
 * no fault of anybody's; an alert here would cry every day of the month.
 */
export function CompletionCell({
  complete,
  workingDays,
  strongSides = [],
}: CompletionCellProps) {
  const strong = new Set(strongSides);
  const left = workingDays - complete;

  return (
    <td
      title={
        left > 0
          ? `${complete} jours complets sur ${workingDays} jours ouvrés — il en reste ${left} à saisir`
          : `Les ${workingDays} jours ouvrés du mois sont saisis`
      }
      className={[
        "h-9 w-14 border-r border-b bg-slate-50 text-center text-sm whitespace-nowrap",
        "text-slate-600 tabular-nums",
        strong.has("right") ? "border-r-slate-500" : "border-r-slate-300",
        strong.has("bottom") ? "border-b-slate-500" : "border-b-slate-300",
      ].join(" ")}
    >
      <span className="font-semibold text-slate-800">{complete}</span>
      <span className="text-slate-400">/{workingDays}</span>
    </td>
  );
}

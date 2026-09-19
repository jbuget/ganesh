import { formatSpelledDate } from "@/lib/dates";
import { slippage, slippageLabel } from "@/lib/planning";

interface LandingDateProps {
  /** The day the projection lands the mission. Null when it never does. */
  endsOn: string | null;
  /** Days between that landing and the date the team announced. */
  slippageDays: number | null;
  /** Whether the server counted that landing as late. */
  isLate: boolean;
}

/**
 * When a mission lands, and how that sits against the date announced.
 *
 * The same grammar as everywhere else: a coloured mark, then the date in
 * ordinary text. The mark is what one scans down the column — green, amber,
 * red — and the date is what one reads once the eye has stopped.
 */
const MARKS: Record<string, string> = {
  none: "bg-slate-300",
  early: "bg-emerald-500",
  "on-time": "bg-emerald-500",
  late: "bg-red-500",
};

export function LandingDate({ endsOn, slippageDays, isLate }: LandingDateProps) {
  if (endsOn === null) {
    return <span className="text-sm text-slate-400">—</span>;
  }

  const state = slippage(slippageDays, isLate);

  return (
    <span className="flex items-center gap-2">
      <span aria-hidden className={`size-2 shrink-0 rounded-full ${MARKS[state]}`} />
      <span className="text-sm text-slate-700">{formatSpelledDate(endsOn)}</span>
      {slippageDays !== null && (
        <span
          className={[
            "text-xs",
            state === "late" ? "font-medium text-red-600" : "text-slate-500",
          ].join(" ")}
        >
          {slippageLabel(slippageDays, isLate)}
        </span>
      )}
    </span>
  );
}

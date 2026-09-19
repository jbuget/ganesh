import { formatWeek } from "@/lib/dates";

interface WeekColumnHeaderProps {
  /** The Monday the week is named by, in ISO format. */
  week: string;
  /** Whether this week opens a new month, which the label then announces. */
  opensMonth?: boolean;
  monthLabel?: string;
}

/**
 * One week column of the plan.
 *
 * Twenty-six of them line up across a six-month horizon: only the day and the
 * abbreviated month fit. The month is spelled out again on the week that opens
 * it, so one can place oneself in the year without counting columns.
 */
export function WeekColumnHeader({
  week,
  opensMonth = false,
  monthLabel,
}: WeekColumnHeaderProps) {
  return (
    <div className="flex flex-col items-center gap-0.5">
      <span
        className={
          opensMonth
            ? "text-[10px] font-medium text-slate-500"
            : "text-[10px] text-transparent"
        }
      >
        {opensMonth ? monthLabel : "."}
      </span>
      <span className="text-xs font-normal text-slate-600">{formatWeek(week)}</span>
    </div>
  );
}

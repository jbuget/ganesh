import type { ProjectStatus } from "@/lib/api/generated/model";
import { formatSpelledDate } from "@/lib/dates";

interface GoLiveDateProps {
  /** The day the team announced. Null while none has been posted. */
  date: string | null | undefined;
  /** Where the mission stands: a service already running is never late. */
  status: ProjectStatus | null | undefined;
  /** One reference day for the whole table, so two rows never disagree. */
  today: Date;
}

/** The day, as the announced dates are written: `2026-11-15`. */
function isoDay(day: Date): string {
  return [
    day.getFullYear(),
    String(day.getMonth() + 1).padStart(2, "0"),
    String(day.getDate()).padStart(2, "0"),
  ].join("-");
}

/**
 * The day a mission is announced for, and whether that day has gone by.
 *
 * A mission nobody has dated leaves the cell empty rather than drawing a
 * placeholder: only what can be read belongs in a table. Nothing is invented
 * here either — the announced date is the team's word, never a projection.
 *
 * Lateness is said in words as well as in colour: the row already carries
 * three coloured marks, and a fourth signal a colour-blind reader could not
 * see would be no signal at all. A service in operations is never late,
 * whatever its date says: it has landed.
 */
export function GoLiveDate({ date, status, today }: GoLiveDateProps) {
  if (!date) return null;

  const isLate = status !== "operations" && date.slice(0, 10) < isoDay(today);

  return (
    <span className="flex items-baseline gap-1.5">
      <span
        className={
          isLate ? "text-sm font-medium text-red-600" : "text-sm text-slate-600"
        }
      >
        {formatSpelledDate(date)}
      </span>
      {isLate && <span className="text-xs text-red-600">en retard</span>}
    </span>
  );
}

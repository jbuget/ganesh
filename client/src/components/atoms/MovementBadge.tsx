import { formatMovement } from "@/lib/activity";

interface MovementBadgeProps {
  /** Days gained or lost against the window before. */
  days: number;
  /** Whether the mission received nothing at all over the window before. */
  isNew?: boolean;
  /** What is being compared against, for whoever reads with a screen reader. */
  against: string;
}

/**
 * How a mission moved since the window before it.
 *
 * What turns a table into a reading: nobody needs to be told « 12 jours sur
 * NOMAD », they need to be told it is three days down. A mission appearing
 * is said apart from one growing — they are two different pieces of news.
 *
 * A mission that did not move reads « stable » rather than empty: an empty
 * cell is indistinguishable from one nobody could fill.
 */
export function MovementBadge({ days, isNew = false, against }: MovementBadgeProps) {
  if (isNew && days > 0) {
    return (
      <span className="rounded bg-sky-50 px-1.5 py-0.5 text-xs font-medium text-sky-700">
        nouveau
      </span>
    );
  }

  const movement = formatMovement(days);
  if (movement === null) {
    return <span className="text-xs text-slate-400">stable</span>;
  }

  return (
    <span
      className={`text-xs font-medium tabular-nums ${
        days > 0 ? "text-emerald-700" : "text-red-700"
      }`}
    >
      {movement}
      <span className="sr-only"> par rapport à {against}</span>
    </span>
  );
}

import { formatMovement } from "@/lib/activity";

interface MovementBadgeProps {
  /** Days gained or lost against the window before. */
  days: number;
  /** Whether the mission received nothing at all over the window before. */
  isNew?: boolean;
}

/**
 * How a mission moved since the window before it.
 *
 * What turns a table into a reading: nobody needs to be told « 12 jours sur
 * NOMAD », they need to be told it is three days down. A mission appearing
 * is said apart from one growing — they are two different pieces of news.
 *
 * Nothing is drawn when nothing moved: a « +0 j » would claim a stability
 * that is only an absence of change.
 */
export function MovementBadge({ days, isNew = false }: MovementBadgeProps) {
  if (isNew && days > 0) {
    return (
      <span className="rounded bg-sky-50 px-1.5 py-0.5 text-xs font-medium text-sky-700">
        nouveau
      </span>
    );
  }

  const movement = formatMovement(days);
  if (movement === null) return null;

  return (
    <span
      className={`text-xs font-medium tabular-nums ${
        days > 0 ? "text-emerald-700" : "text-red-700"
      }`}
    >
      {movement}
      <span className="sr-only"> par rapport à la période précédente</span>
    </span>
  );
}

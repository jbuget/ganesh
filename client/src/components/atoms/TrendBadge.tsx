import { formatPoints } from "@/lib/statistics";

interface TrendBadgeProps {
  /** Movement in percentage points, or null without a comparable window. */
  points: number | null | undefined;
}

/**
 * How the lead figure moved against the window before it.
 *
 * A rate says little on its own and much once it is read as moving. Nothing is
 * drawn when there is nothing to compare against: inventing a « +0 pt » would
 * claim a stability that was never measured.
 */
export function TrendBadge({ points }: TrendBadgeProps) {
  if (points === null || points === undefined) return null;

  const isFlat = Math.round(points * 10) === 0;
  const tone = isFlat
    ? "bg-slate-100 text-slate-600"
    : points > 0
      ? "bg-emerald-50 text-emerald-700"
      : "bg-red-50 text-red-700";

  return (
    <span
      role="status"
      aria-describedby="trend-reference"
      className={`rounded px-1.5 py-0.5 text-sm font-medium tabular-nums ${tone}`}
    >
      {isFlat ? "stable" : formatPoints(points)}
      <span id="trend-reference" className="sr-only">
        par rapport à la période précédente
      </span>
    </span>
  );
}

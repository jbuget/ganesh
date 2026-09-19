import { formatDecimalDays } from "@/lib/dates";

interface MissionLoadCellProps {
  /** Days the projection placed on this mission during this week. */
  days: number;
}

/**
 * One week of one mission, as a block whose weight follows the days placed.
 *
 * Read across a row, the blocks draw the span the mission occupies: the bar a
 * gantt would have shown, except that nobody drew it by hand — it comes out of
 * the room the diaries actually leave.
 *
 * A week the mission does not occupy stays empty rather than showing a zero:
 * the eye must catch the span, and a row of zeros would bury it.
 */
export function MissionLoadCell({ days }: MissionLoadCellProps) {
  if (days <= 0) return <div className="h-6" />;

  // Five days is a full week; below that the block lightens in proportion, so
  // a half-time week never reads like a full one.
  const weight = Math.min(1, days / 5);

  return (
    <div className="flex h-6 items-center justify-center">
      <div
        className="flex h-6 w-full items-center justify-center rounded-sm bg-sky-500 text-[11px] font-medium text-white tabular-nums"
        style={{ opacity: 0.35 + weight * 0.65 }}
        title={`${formatDecimalDays(days)} j cette semaine`}
      >
        {formatDecimalDays(days)}
      </div>
    </div>
  );
}

import type { MoodLevel } from "@/lib/api/generated/model";
import { MOODS } from "@/lib/mood";

interface MoodDistributionBarProps {
  /** How many of each level. A level the API left out is a level at zero. */
  counts: Partial<Record<MoodLevel, number>>;
  participation: number;
}

/**
 * How a day was spread, as one bar cut into five.
 *
 * The one place the application fills a surface: a chart is read by area, and
 * a mark alone could not say that half a day went badly. It is the grammar
 * `ShareBar` already uses, and it stops there.
 *
 * The segments run in the order of the scale, worst on the left: a day drifting
 * is a bar whose colour slides left, and the eye catches the slide down a
 * column before it reads any single figure.
 */
export function MoodDistributionBar({
  counts,
  participation,
}: MoodDistributionBarProps) {
  if (participation === 0) {
    return (
      <div className="h-2.5 rounded-full bg-slate-100" aria-label="Aucune réponse" />
    );
  }

  return (
    <div className="flex h-2.5 overflow-hidden rounded-full bg-slate-100">
      {MOODS.map((level) => {
        const count = counts[level.value] ?? 0;
        if (count === 0) return null;

        return (
          <span
            key={level.value}
            title={`${level.label} : ${count}`}
            style={{ width: `${(count / participation) * 100}%` }}
            className={level.fill}
          />
        );
      })}
    </div>
  );
}

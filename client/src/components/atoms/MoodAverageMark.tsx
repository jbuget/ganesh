import { MOODS, levelAt } from "@/lib/mood";
import { NOTHING } from "@/lib/statistics";

interface MoodAverageMarkProps {
  /** The mean of the day's answers, or null when nobody answered. */
  average: number | null;
}

/** Ends of the scale the mark travels along. */
const LOWEST = 1;
const HIGHEST = MOODS.length;

/**
 * Where a day's mean sits on the scale: a dot on a track, then the figure.
 *
 * The dot is what makes the fortnight a trend. Read down the column, the dots
 * draw the line a chart would have drawn — without a chart library, and
 * without the curve of averages crossing the bars it is supposed to sum up.
 *
 * A day nobody answered leaves the track empty rather than dropping the dot to
 * the floor: silence is not a bad day, and a line falling through it would say
 * it was.
 */
export function MoodAverageMark({ average }: MoodAverageMarkProps) {
  if (average === null) {
    return (
      <div className="flex items-center gap-2">
        <div className="h-px flex-1 bg-slate-200" />
        <span className="w-8 text-right text-sm tabular-nums text-slate-300">
          {NOTHING}
        </span>
      </div>
    );
  }

  const level = levelAt(average);
  const share = ((average - LOWEST) / (HIGHEST - LOWEST)) * 100;

  return (
    <div className="flex items-center gap-2">
      <div className="relative h-px flex-1 bg-slate-200">
        <span
          style={{ left: `${share}%` }}
          className={`absolute top-1/2 size-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full ${level.fill}`}
          aria-hidden
        />
      </div>
      <span className="w-8 text-right text-sm tabular-nums text-slate-700">
        {average.toFixed(1).replace(".", ",")}
      </span>
    </div>
  );
}

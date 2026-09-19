import type { MoodLevel } from "@/lib/api/generated/model";
import { mood } from "@/lib/mood";

interface MoodBubbleProps {
  level: MoodLevel;
  /** How many answered this level on this day. Nothing is drawn at zero. */
  count: number;
  /** The busiest cell of the chart, which the sizes are read against. */
  busiest: number;
}

/** Small enough to stay visible, large enough to stay inside its row. */
const SMALLEST = 10;
const LARGEST = 44;

/**
 * One cell of the chart: as many answers, as much surface.
 *
 * The radius follows the square root of the count, not the count itself. A
 * circle twice as wide covers four times the area, and the eye reads the area:
 * scaling the radius straight would make four answers look like sixteen.
 *
 * Sizes are read against the busiest cell rather than against the headcount:
 * what one looks for on this chart is where the answers gathered, and a team
 * of twenty answering three times would otherwise draw nothing but dust.
 */
export function MoodBubble({ level, count, busiest }: MoodBubbleProps) {
  const shade = mood(level);
  if (count === 0 || !shade) return null;

  const size =
    busiest <= 1
      ? LARGEST
      : SMALLEST + (LARGEST - SMALLEST) * Math.sqrt(count / busiest);

  return (
    <span
      style={{ width: size, height: size }}
      className={`block shrink-0 rounded-full opacity-70 ${shade.fill}`}
      aria-hidden
    />
  );
}

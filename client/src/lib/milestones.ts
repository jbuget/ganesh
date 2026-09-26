import { isoDay } from "@/lib/dates";

/**
 * Whether a milestone's day has gone by without it happening.
 *
 * Its own reading rather than `isGoLiveLate`'s, and the difference is the
 * whole point: a mission is excused by its phase — a service in operations
 * has landed — where a milestone is excused by one thing only, having been
 * reached. It carries no phase to read, and the day it happened is the fact
 * that settles it.
 */
export function isMilestoneLate(
  expectedOn: string,
  reachedOn: string | null | undefined,
  today: Date,
): boolean {
  if (reachedOn) return false;
  return expectedOn.slice(0, 10) < isoDay(today);
}

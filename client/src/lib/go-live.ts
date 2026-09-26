import type { ProjectStatus } from "@/lib/api/generated/model";
import { isoDay } from "@/lib/dates";

/**
 * Whether the day a mission was announced for has gone by.
 *
 * Written once and read by every screen that shows the date — the reference
 * list, the roadmap, the sheet of a project — so that three screens cannot
 * come to disagree about which missions are late.
 *
 * Two readings it holds. A mission nobody has dated is never late: there is
 * no commitment to be late against, and inventing one would put a red mark on
 * the missions the team has been most honest about. And a service in
 * operations is never late whatever its date says: it has landed, and the
 * announced day is now its history.
 */
export function isGoLiveLate(
  date: string | null | undefined,
  status: ProjectStatus | null | undefined,
  today: Date,
): boolean {
  if (!date) return false;
  return status !== "operations" && date.slice(0, 10) < isoDay(today);
}

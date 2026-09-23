"use client";

import { useTeamMoods } from "@/lib/api/queries";
import { todayIso } from "@/lib/dates";

/**
 * State of the team morale screen.
 *
 * It reads and never writes, and that is the rule the rest was built around:
 * a screen that both showed the team and let one answer would put the answer
 * under the eyes of what it is about.
 *
 * One answers from the home screen, or from the reminder that comes round at
 * the end of the afternoon — which is what lets this screen go on refusing.
 * The reminder deliberately keeps away from here.
 */
export function useTeamMoodScreen() {
  const { window, isLoading } = useTeamMoods();

  return {
    isLoading,
    today: todayIso(),
    /** The days of the window, the most recent first. */
    days: window?.days ?? [],
    /** Active teammates, against which participation is read. */
    headcount: window?.headcount ?? 0,
  };
}

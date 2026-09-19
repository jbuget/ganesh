"use client";

import { useTeamMoods } from "@/lib/api/queries";
import { todayIso } from "@/lib/dates";

/**
 * State of the team morale screen.
 *
 * It reads and never writes: one answers for one's own day from the home
 * screen, and nowhere else. A screen that both showed the team and let one
 * answer would put the answer under the eyes of what it is about.
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

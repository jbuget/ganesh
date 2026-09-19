"use client";

import { useQueryClient } from "@tanstack/react-query";

import { useCurrentUser, useMonthGrid, useProjects } from "@/lib/api/queries";
import { firstDayOfMonth, previousMonth, todayIso } from "@/lib/dates";
import {
  daysMissingEntry,
  latestUpdates,
  monthsToSettle,
  myMissions,
} from "@/lib/home";
import { missionsToDeclare } from "@/lib/missions";

/** How far the news feed goes back: what is new, not the whole archive. */
const FEED_LENGTH = 8;

/**
 * State of the home screen.
 *
 * It reads four months: the one running, which says what is left to enter, and
 * the three gone by, which say what was left behind. Three is the horizon the
 * team steers on — past that, a month is a matter for a manager, not a
 * reminder on a home screen.
 *
 * Nothing is written from here — the screen names what there is to do and
 * hands over to the screen that does it.
 */
export function useHome() {
  const today = todayIso();
  const cursor = {
    year: Number(today.slice(0, 4)),
    month: Number(today.slice(5, 7)),
  };
  const previous = previousMonth(cursor.year, cursor.month);
  const beforeThat = previousMonth(previous.year, previous.month);
  const oldest = previousMonth(beforeThat.year, beforeThat.month);

  const { user: me } = useCurrentUser();
  const enabled = Boolean(me?.id);

  const current = useMonthGrid(
    firstDayOfMonth(cursor.year, cursor.month),
    null,
    enabled,
  );
  // One call per watched month, written out rather than looped: hooks are not
  // called from a loop, and three is the whole horizon.
  const gone = useMonthGrid(
    firstDayOfMonth(previous.year, previous.month),
    null,
    enabled,
  );
  const goneBefore = useMonthGrid(
    firstDayOfMonth(beforeThat.year, beforeThat.month),
    null,
    enabled,
  );
  const goneLongest = useMonthGrid(
    firstDayOfMonth(oldest.year, oldest.month),
    null,
    enabled,
  );
  const { missions } = useProjects();
  const queryClient = useQueryClient();

  const mine = myMissions(missions, me?.id ?? null, current.grid, gone.grid);
  const declared = current.grid?.rows.map((row) => row.project_id) ?? [];

  return {
    me,
    cursor,
    // Every month counts towards it: the reminders are read as one list, and a
    // month landing after the others would make one appear under a panel the
    // reader has already gone through.
    isLoading:
      current.isLoading ||
      gone.isLoading ||
      goneBefore.isLoading ||
      goneLongest.isLoading,

    /** Replays the screen's queries — a phase changed in the panel shows here. */
    async refresh() {
      await queryClient.invalidateQueries();
    },

    /** What the month carries, delivered told from forecast as everywhere else. */
    actualDays: current.grid?.actual_total ?? 0,
    forecastDays: current.grid?.forecast_total ?? 0,
    workingDays: current.grid?.working_days ?? 0,

    /** The months gone by still open, the closest one first. */
    monthsToSettle: monthsToSettle([
      { cursor: previous, grid: gone.grid },
      { cursor: beforeThat, grid: goneBefore.grid },
      { cursor: oldest, grid: goneLongest.grid },
    ]),

    daysMissing: daysMissingEntry(current.grid, today),
    missionsToDeclare: missionsToDeclare(missions, me?.id ?? null, declared),

    mine,
    updates: latestUpdates(mine, FEED_LENGTH),
  };
}

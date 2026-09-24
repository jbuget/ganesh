"use client";

import { useQueryClient } from "@tanstack/react-query";

import {
  addMissionToMonth,
  clearEntry,
  removeMissionFromMonth,
  setEntry,
} from "@/lib/api/generated/entries/entries";
import type { ProjectResponse } from "@/lib/api/generated/model";
import { useReopenMonth, useValidateMonth } from "@/lib/api/generated/months/months";
import { useCreateProject } from "@/lib/api/generated/projects/projects";
import {
  mutationResult,
  useCurrentUser,
  useMonthGrid,
  useProjects,
  useTeammates,
} from "@/lib/api/queries";
import type { DayValue } from "@/lib/day-value";
import {
  firstDayOfMonth,
  monthParam,
  nextMonth,
  parseMonthParam,
  previousMonth,
  todayIso,
} from "@/lib/dates";
import { assignedMissionIds, missionsToDeclare } from "@/lib/missions";
import { withPendingEntries } from "@/lib/pending-entries";
import { useQueryString, writeUrl } from "@/lib/url-state";
import { usePendingEntries } from "@/lib/use-pending-entries";
import { holds } from "@/lib/roles";
import { useMayWrite } from "@/lib/use-may-write";

/**
 * State and actions of a month's entry screen.
 *
 * All the coordination lives here — navigation, data, writes — so the component
 * carries nothing but the rendering.
 */
export function useTimesheetMonth() {
  const today = todayIso();
  // The month lives in the address, like the open panel: a reminder on the home
  // screen links straight to the month it speaks of, and a month is shared by a
  // link. Absent, it is the month running — which is what one comes for.
  const query = useQueryString();
  const params = new URLSearchParams(query);
  const cursor = parseMonthParam(params.get("month")) ?? {
    year: Number(today.slice(0, 4)),
    month: Number(today.slice(5, 7)),
  };
  // The teammate being looked at lives in the address too, and under the same
  // name as on the teammate list: a colleague's month is reached by a link —
  // from their panel, from a reminder — and must survive a reload.
  const viewedUserId = Number(params.get("user")) || null;

  const queryClient = useQueryClient();
  const month = firstDayOfMonth(cursor.year, cursor.month);

  const { user: me } = useCurrentUser();
  const mayWrite = useMayWrite();
  const { teammates } = useTeammates();
  const { missions, projects } = useProjects();
  const createProject = useCreateProject();
  const validateMonth = useValidateMonth();
  const reopenMonth = useReopenMonth();

  const gridQuery = useMonthGrid(month, viewedUserId, Boolean(me?.id));

  async function refresh() {
    await queryClient.invalidateQueries();
  }

  const target = viewedUserId ? { user_id: viewedUserId } : undefined;

  /**
   * Clicks are answered on the spot and written once they have settled: a half
   * day is two clicks on one cell, and one write.
   *
   * The cell names whose month it is in, so a write still waiting when one
   * walks to a colleague's month goes where it was clicked.
   */
  const entries = usePendingEntries({
    async write({ userId, projectId, day }, value) {
      const whose = userId === me?.id ? undefined : { user_id: userId };
      if (value === 0) {
        await clearEntry({ project_id: projectId, day, ...whose });
      } else {
        await setEntry({ project_id: projectId, day, value }, whose);
      }
    },
    refresh,
  });

  /** What the server holds, the cells awaiting their write laid over it. */
  const grid = gridQuery.grid
    ? withPendingEntries(gridQuery.grid, entries.pending, today)
    : gridQuery.grid;

  /** Changing month is a navigation: going back must bring the previous one. */
  function goToMonth(next: { year: number; month: number }) {
    writeUrl((params) => params.set("month", monthParam(next)));
  }

  const isOwnMonth = viewedUserId === null || viewedUserId === me?.id;
  const targetUserId = viewedUserId ?? me?.id ?? null;
  const isCurrentMonth =
    cursor.year === Number(today.slice(0, 4)) &&
    cursor.month === Number(today.slice(5, 7));

  /** Missions already in the grid, not to be offered again. */
  const displayedProjectIds = grid?.rows.map((row) => row.project_id) ?? [];

  return {
    today,
    cursor,
    month,
    grid,
    isLoading: gridQuery.isLoading,
    teammates,
    projects,
    /** Replays the month's queries — what a panel edit changes shows here. */
    refresh,

    targetUserId,
    currentUserId: me?.id ?? null,
    isOwnMonth,

    /** Whose month is shown, when it is not one's own. */
    viewedTeammateName: isOwnMonth
      ? null
      : (teammates.find((user) => user.id === viewedUserId)?.display_name ?? null),

    /**
     * The two gestures a month is committed or given back with.
     *
     * They never cross, and neither depends on the dimension the other reads:
     * validating is about the month being one's own, whatever the role;
     * reopening is about being a manager, whoever the month belongs to. The
     * state of the month is what tells them apart, so they never show together.
     */
    /**
     * Whether this month accepts the person reading.
     *
     * Two things at once, and both have to hold: the month is open, and the
     * reader is not a guest. The screen asks this rather than `is_writable`,
     * which says what is true of the *month* — a guest reading an open month
     * would otherwise be offered every cell of it.
     */
    writable: Boolean(grid?.is_writable) && mayWrite,

    canValidate: Boolean(grid?.is_writable) && isOwnMonth && mayWrite,
    canReopen: Boolean(grid && !grid.is_writable) && holds(me?.role, "MANAGER"),

    /** Missions the viewer contributes to, offered first when adding a row. */
    assignedIds: assignedMissionIds(missions, me?.id ?? null),

    /**
     * Missions one was put on with nothing declared on them.
     *
     * Only on one's own month, and only on the month running: an assignment
     * carries no date, so it says what holds today and nothing about a month
     * gone by. Reading it into September in December would be inventing.
     */
    missionsToDeclare:
      isOwnMonth && isCurrentMonth
        ? missionsToDeclare(missions, me?.id ?? null, displayedProjectIds)
        : [],

    displayedProjectIds,

    goToPreviousMonth() {
      goToMonth(previousMonth(cursor.year, cursor.month));
    },

    goToNextMonth() {
      goToMonth(nextMonth(cursor.year, cursor.month));
    },

    /** Looking at someone else's month is a navigation: going back returns. */
    viewTeammate(userId: number) {
      writeUrl((params) => {
        if (userId === me?.id) params.delete("user");
        else params.set("user", String(userId));
      });
    },

    /**
     * Takes a cell's new value. A `0` removes the entry, any other writes it.
     *
     * Nothing leaves at once: the write goes out when the clicking has stopped,
     * and the grid reads the value in the meantime.
     */
    setDayValue(projectId: number, day: string, value: DayValue) {
      if (targetUserId === null) return;
      entries.setValue({ userId: targetUserId, projectId, day }, value);
    },

    /**
     * Puts a mission on the month, with nothing entered on it yet.
     *
     * The row is written server-side straight away: lining up what one is
     * about to work on is a gesture of its own, and it must still be there
     * after a reload.
     */
    async addMission(projectId: number) {
      await addMissionToMonth({ project_id: projectId, month }, target);
      await refresh();
    },

    /** Removes a mission from the month, with the time it carries. */
    async removeMission(projectId: number) {
      // A cell still waiting would write itself back onto a row that has gone.
      await entries.flush();
      await removeMissionFromMonth({ project_id: projectId, month, ...target });
      await refresh();
    },

    async declareProject(label: string) {
      const created = await createProject.mutateAsync({
        data: { label, kind: "project", status: "exploration" },
      });
      await addMissionToMonth(
        { project_id: mutationResult<ProjectResponse>(created).id, month },
        target,
      );
      await refresh();
    },

    async validate() {
      // The month closes to writes: what is waiting goes out before it does,
      // or it would be refused and lost.
      await entries.flush();
      await validateMonth.mutateAsync({ month });
      await refresh();
    },

    /**
     * Gives a validated month back to entry. Managers only.
     *
     * The month reopened is the one shown, which the selector names: unlike
     * validation, the route has to be told whose it is.
     */
    async reopen() {
      if (targetUserId === null) return;
      await reopenMonth.mutateAsync({ month, params: { user_id: targetUserId } });
      await refresh();
    },
  };
}

"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import {
  addMissionToMonth,
  clearEntry,
  removeMissionFromMonth,
  setEntry,
} from "@/lib/api/generated/entries/entries";
import type { ProjectResponse } from "@/lib/api/generated/model";
import { useValidateMonth } from "@/lib/api/generated/months/months";
import { useCreateProject } from "@/lib/api/generated/projects/projects";
import {
  mutationResult,
  useCurrentUser,
  useMonthGrid,
  useProjects,
  useTeammates,
} from "@/lib/api/queries";
import type { DayValue } from "@/lib/day-value";
import { firstDayOfMonth, nextMonth, previousMonth } from "@/lib/dates";
import { assignedMissionIds, missionsToDeclare } from "@/lib/missions";

/** Today's date in local time: `toISOString` would return yesterday in the evening. */
export function todayIso(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

/**
 * State and actions of a month's entry screen.
 *
 * All the coordination lives here — navigation, data, writes — so the component
 * carries nothing but the rendering.
 */
export function useTimesheetMonth() {
  const today = todayIso();
  const [cursor, setCursor] = useState(() => ({
    year: Number(today.slice(0, 4)),
    month: Number(today.slice(5, 7)),
  }));
  const [viewedUserId, setViewedUserId] = useState<number | null>(null);

  const queryClient = useQueryClient();
  const month = firstDayOfMonth(cursor.year, cursor.month);

  const { user: me } = useCurrentUser();
  const { teammates } = useTeammates();
  const { missions, projects } = useProjects();
  const createProject = useCreateProject();
  const validateMonth = useValidateMonth();

  const gridQuery = useMonthGrid(month, viewedUserId, Boolean(me?.id));
  const grid = gridQuery.grid;

  const target = viewedUserId ? { user_id: viewedUserId } : undefined;

  async function refresh() {
    await queryClient.invalidateQueries();
  }

  const isOwnMonth = viewedUserId === null || viewedUserId === me?.id;
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

    targetUserId: viewedUserId ?? me?.id ?? null,
    currentUserId: me?.id ?? null,
    isOwnMonth,

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
      setCursor(previousMonth(cursor.year, cursor.month));
    },

    goToNextMonth() {
      setCursor(nextMonth(cursor.year, cursor.month));
    },

    viewTeammate(userId: number) {
      setViewedUserId(userId === me?.id ? null : userId);
    },

    /** A null value removes the entry; any other value writes it. */
    async setDayValue(projectId: number, day: string, value: DayValue) {
      if (value === 0) {
        await clearEntry({ project_id: projectId, day, ...target });
      } else {
        await setEntry({ project_id: projectId, day, value: value }, target);
      }
      await refresh();
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
      await validateMonth.mutateAsync({ month });
      await refresh();
    },
  };
}

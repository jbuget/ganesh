"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import {
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

/** Date du jour en heure locale : `toISOString` renverrait la veille en soiree. */
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
  const [extraRows, setExtraRows] = useState<ProjectResponse[]>([]);

  const queryClient = useQueryClient();
  const month = firstDayOfMonth(cursor.year, cursor.month);

  const { user: me } = useCurrentUser();
  const { teammates } = useTeammates();
  const { projects } = useProjects();
  const createProject = useCreateProject();
  const validateMonth = useValidateMonth();

  const gridQuery = useMonthGrid(month, viewedUserId, Boolean(me?.id));
  const grid = gridQuery.grid;

  const target = viewedUserId ? { user_id: viewedUserId } : undefined;

  async function refresh() {
    await queryClient.invalidateQueries();
  }

  return {
    today,
    cursor,
    month,
    grid,
    isLoading: gridQuery.isLoading,
    teammates,
    projects,
    extraRows,

    targetUserId: viewedUserId ?? me?.id ?? null,
    currentUserId: me?.id ?? null,
    isOwnMonth: viewedUserId === null || viewedUserId === me?.id,

    /** Missions already in the grid, not to be offered again. */
    displayedProjectIds: [
      ...(grid?.rows.map((row) => row.project_id) ?? []),
      ...extraRows.map((project) => project.id),
    ],

    goToPreviousMonth() {
      setCursor(previousMonth(cursor.year, cursor.month));
      setExtraRows([]);
    },

    goToNextMonth() {
      setCursor(nextMonth(cursor.year, cursor.month));
      setExtraRows([]);
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

    addMission(projectId: number) {
      const project = projects.find((p) => p.id === projectId);
      if (project) setExtraRows((rows) => [...rows, project]);
    },

    /**
     * Removes a mission from the month, with the time it carries.
     *
     * A row added but still empty exists locally only: there is nothing to ask
     * the server to make it disappear.
     */
    async removeMission(projectId: number) {
      setExtraRows((rows) => rows.filter((row) => row.id !== projectId));
      if (grid?.rows.some((row) => row.project_id === projectId)) {
        await removeMissionFromMonth({ project_id: projectId, month, ...target });
        await refresh();
      }
    },

    async declareProject(label: string) {
      const created = await createProject.mutateAsync({
        data: { label, kind: "project", status: "exploration" },
      });
      setExtraRows((rows) => [...rows, mutationResult<ProjectResponse>(created)]);
      await refresh();
    },

    async validate() {
      await validateMonth.mutateAsync({ month });
      await refresh();
    },
  };
}

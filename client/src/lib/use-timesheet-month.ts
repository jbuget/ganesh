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
 * Etat et actions de l'ecran de saisie d'un mois.
 *
 * Toute la coordination vit ici — navigation, donnees, ecritures — pour que le
 * composant ne porte plus que le rendu.
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
  const mois = firstDayOfMonth(cursor.year, cursor.month);

  const { user: me } = useCurrentUser();
  const { teammates } = useTeammates();
  const { projects } = useProjects();
  const createProject = useCreateProject();
  const validateMonth = useValidateMonth();

  const gridQuery = useMonthGrid(mois, viewedUserId, Boolean(me?.id));
  const grid = gridQuery.grid;

  const target = viewedUserId ? { user_id: viewedUserId } : undefined;

  async function refresh() {
    await queryClient.invalidateQueries();
  }

  return {
    today,
    cursor,
    mois,
    grid,
    isLoading: gridQuery.isLoading,
    teammates,
    projects,
    extraRows,

    targetUserId: viewedUserId ?? me?.id ?? null,
    currentUserId: me?.id ?? null,
    isOwnMonth: viewedUserId === null || viewedUserId === me?.id,

    /** Missions deja presentes dans la matrice, a ne pas reproposer. */
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

    /** Une valeur nulle retire la saisie ; toute autre valeur l'ecrit. */
    async setDayValue(projectId: number, jour: string, value: DayValue) {
      if (value === 0) {
        await clearEntry({ project_id: projectId, jour, ...target });
      } else {
        await setEntry({ project_id: projectId, jour, valeur: value }, target);
      }
      await refresh();
    },

    addMission(projectId: number) {
      const project = projects.find((p) => p.id === projectId);
      if (project) setExtraRows((rows) => [...rows, project]);
    },

    /**
     * Retire une mission du mois, avec le temps qu'elle porte.
     *
     * Une ligne ajoutee mais encore vide n'existe que localement : il n'y a
     * rien a demander au serveur pour la faire disparaitre.
     */
    async removeMission(projectId: number) {
      setExtraRows((rows) => rows.filter((row) => row.id !== projectId));
      if (grid?.rows.some((row) => row.project_id === projectId)) {
        await removeMissionFromMonth({ project_id: projectId, mois, ...target });
        await refresh();
      }
    },

    async declareProject(label: string) {
      const created = await createProject.mutateAsync({
        data: { label, kind: "projet", statut: "exploration" },
      });
      setExtraRows((rows) => [...rows, mutationResult<ProjectResponse>(created)]);
      await refresh();
    },

    async validate() {
      await validateMonth.mutateAsync({ mois });
      await refresh();
    },
  };
}

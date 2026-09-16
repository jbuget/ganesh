"use client";

import { useQueryClient } from "@tanstack/react-query";

import {
  changeProjectStatus,
  createProject,
  deleteProject,
  importProjects,
  updateProject,
} from "@/lib/api/generated/projects/projects";
import type {
  ImportReportResponse,
  ProjectKind,
  ProjectStatus,
} from "@/lib/api/generated/model";
import { mutationResult, useCurrentUser, useProjects } from "@/lib/api/queries";
import { parseProjectsCsv } from "@/lib/csv-import";
import { buildProjectTree, offProjectActivities } from "@/lib/project-tree";

/**
 * Etat et actions de l'ecran du referentiel.
 *
 * Comme pour la matrice, la coordination vit dans un hook pour que le composant
 * ne porte que le rendu.
 */
export function useProjectsScreen() {
  const queryClient = useQueryClient();
  const { user: me } = useCurrentUser();
  const { projects, isLoading } = useProjects();

  async function refresh() {
    await queryClient.invalidateQueries();
  }

  return {
    isLoading,
    isManager: me?.role === "MANAGER",
    arbre: buildProjectTree(projects),
    activites: offProjectActivities(projects),

    async changeStatus(projectId: number, statut: ProjectStatus) {
      await changeProjectStatus(projectId, { statut });
      await refresh();
    },

    async edit(
      projectId: number,
      edits: { label: string; estime_j: number | null; monday_item_id: string | null },
    ) {
      await updateProject(projectId, edits);
      await refresh();
    },

    async setEstimate(projectId: number, estime_j: number | null) {
      await updateProject(projectId, { estime_j });
      await refresh();
    },

    async remove(projectId: number) {
      await deleteProject(projectId);
      await refresh();
    },

    async archive(projectId: number, actif: boolean) {
      await updateProject(projectId, { actif });
      await refresh();
    },

    async declare(label: string, kind: ProjectKind, parentId?: number) {
      const cree = await createProject({
        label,
        kind,
        statut: "exploration",
        ...(parentId ? { parent_id: parentId } : {}),
      });
      await refresh();
      return mutationResult(cree);
    },

    async importCsv(contenu: string): Promise<ImportReportResponse> {
      const rapport = await importProjects({ lignes: parseProjectsCsv(contenu) });
      await refresh();
      return mutationResult<ImportReportResponse>(rapport);
    },
  };
}

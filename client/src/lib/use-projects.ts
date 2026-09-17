"use client";

import { useQueryClient } from "@tanstack/react-query";

import { createProject, importProjects } from "@/lib/api/generated/projects/projects";
import type { ImportReportResponse, ProjectKind } from "@/lib/api/generated/model";
import { mutationResult, useCurrentUser, useProjects } from "@/lib/api/queries";
import { parseProjectsCsv } from "@/lib/csv-import";
import {
  AUCUN_FILTRE,
  filtrerMissions,
  inclutLesArchivees,
  type MissionFilters,
} from "@/lib/mission-filters";
import { buildProjectTree, offProjectActivities } from "@/lib/project-tree";

/**
 * Etat et actions de l'ecran du referentiel.
 *
 * Comme pour la matrice, la coordination vit dans un hook pour que le composant
 * ne porte que le rendu. Le filtrage en fait partie : l'ecran recoit les
 * criteres et rend l'arborescence deja reduite, sans avoir a savoir comment.
 */
export function useProjectsScreen(filtres: MissionFilters = AUCUN_FILTRE) {
  const queryClient = useQueryClient();
  const { user: me } = useCurrentUser();
  const { missions, isLoading } = useProjects(inclutLesArchivees(filtres));
  const retenues = filtrerMissions(missions, filtres);

  async function refresh() {
    await queryClient.invalidateQueries();
  }

  return {
    isLoading,
    isManager: me?.role === "MANAGER",
    arbre: buildProjectTree(retenues),
    activites: offProjectActivities(retenues),

    /** Missions retenues, et missions que le referentiel porte en tout. */
    visibles: retenues.length,
    total: missions.length,

    /** Relit le referentiel apres une modification faite dans le panneau. */
    refresh,

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

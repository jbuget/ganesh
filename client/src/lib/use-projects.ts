"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useState } from "react";

import { createProject, importProjects } from "@/lib/api/generated/projects/projects";
import type { ImportReportResponse, ProjectKind } from "@/lib/api/generated/model";
import { mutationResult, useCurrentUser, useProjects } from "@/lib/api/queries";
import { parseProjectsCsv } from "@/lib/csv-import";
import {
  NO_FILTER,
  filtrerMissions,
  inclutLesArchivees,
  type MissionFilters,
} from "@/lib/mission-filters";
import { NO_SORT, type MissionSort } from "@/lib/mission-sort";
import { buildProjectTree, offProjectActivities } from "@/lib/project-tree";

/**
 * Etat et actions de l'ecran du referentiel.
 *
 * Comme pour la matrice, la coordination vit dans un hook pour que le composant
 * ne porte que le rendu. Le filtrage et le rangement en font partie : l'ecran
 * recoit les criteres et l'ordre, et rend l'arborescence deja reduite et
 * rangee, sans avoir a savoir comment.
 */
export function useProjectsScreen(
  filters: MissionFilters = NO_FILTER,
  sorted: MissionSort = NO_SORT,
) {
  const queryClient = useQueryClient();
  const { user: me } = useCurrentUser();
  const { missions, isLoading } = useProjects(inclutLesArchivees(filters));
  const kept = filtrerMissions(missions, filters);
  // On retient ce qui est deplie, pas ce qui est replie : le referentiel
  // s'ouvre sur ses projets, et les sous-projets se demandent. Une mission
  // creee en cours de route arrive donc repliee, comme les autres.
  const [deplies, setDeplies] = useState<ReadonlySet<number>>(() => new Set());

  const toggle = useCallback((id: number) => {
    setDeplies((actuels) => {
      const next_ones = new Set(actuels);
      if (!next_ones.delete(id)) next_ones.add(id);
      return next_ones;
    });
  }, []);

  async function refresh() {
    await queryClient.invalidateQueries();
  }

  return {
    isLoading,
    isManager: me?.role === "MANAGER",
    tree: buildProjectTree(kept, sorted),
    activities: offProjectActivities(kept),

    /** Missions retenues, et missions que le referentiel porte en tout. */
    visible: kept.length,
    total: missions.length,

    /** Si les sous-projets d'une mission se montrent. */
    estDeplie: (id: number) => deplies.has(id),
    toggle,

    /** Relit le referentiel apres une modification faite dans le panneau. */
    refresh,

    async declare(label: string, kind: ProjectKind, parentId?: number) {
      const cree = await createProject({
        label,
        kind,
        status: "exploration",
        ...(parentId ? { parent_id: parentId } : {}),
      });
      await refresh();
      return mutationResult(cree);
    },

    async importCsv(content: string): Promise<ImportReportResponse> {
      const report = await importProjects({ rows: parseProjectsCsv(content) });
      await refresh();
      return mutationResult<ImportReportResponse>(report);
    },
  };
}

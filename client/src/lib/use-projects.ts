"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useState } from "react";

import { createProject, importProjects } from "@/lib/api/generated/projects/projects";
import type { ImportReportResponse, ProjectKind } from "@/lib/api/generated/model";
import { mutationResult, useCurrentUser, useProjects } from "@/lib/api/queries";
import { parseProjectsCsv } from "@/lib/csv-import";
import {
  NO_FILTER,
  filterMissions,
  inclutLesArchivees,
  type MissionFilters,
} from "@/lib/mission-filters";
import { NO_SORT, type MissionSort } from "@/lib/mission-sort";
import { buildProjectTree, offProjectActivities } from "@/lib/project-tree";

/**
 * State and actions of the reference list screen.
 *
 * As with the grid, coordination lives in a hook so the component carries only
 * the rendering. Filtering and ordering are part of it: the screen receives the
 * criteria and the order, and renders the tree already reduced and arranged,
 * without having to know how.
 */
export function useProjectsScreen(
  filters: MissionFilters = NO_FILTER,
  sorted: MissionSort = NO_SORT,
) {
  const queryClient = useQueryClient();
  const { user: me } = useCurrentUser();
  const { missions, isLoading } = useProjects(inclutLesArchivees(filters));
  const kept = filterMissions(missions, filters);
  // We remember what is expanded, not what is collapsed: the reference list
  // opens on its projects, and sub-projects are asked for. A mission created
  // along the way therefore arrives collapsed, like the others.
  const [expanded, setExpanded] = useState<ReadonlySet<number>>(() => new Set());

  const toggle = useCallback((id: number) => {
    setExpanded((actuels) => {
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

    /** Missions kept, and missions the reference list carries in all. */
    visible: kept.length,
    total: missions.length,

    /** Whether a mission's sub-projects are showing. */
    estDeplie: (id: number) => expanded.has(id),
    toggle,

    /** Reads the reference list again after a change made in the panel. */
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

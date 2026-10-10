"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useState } from "react";

import {
  attachProject,
  createProject,
  importProjects,
  listProjects,
} from "@/lib/api/generated/projects/projects";
import type {
  ImportReportResponse,
  ProjectKind,
  ProjectListItemResponse,
  ProjectResponse,
} from "@/lib/api/generated/model";
import { mutationResult, useCurrentUser, useProjects } from "@/lib/api/queries";
import { parseProjectsCsv } from "@/lib/csv-import";
import {
  NO_FILTER,
  filterMissions,
  includesArchived,
  type MissionFilters,
} from "@/lib/mission-filters";
import { NO_SORT, type MissionSort } from "@/lib/mission-sort";
import { buildProjectTree } from "@/lib/project-tree";
import { holds } from "@/lib/roles";
import { useMayWrite } from "@/lib/use-may-write";

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
  const { missions, isLoading } = useProjects(includesArchived(filters));
  const kept = filterMissions(missions, filters);
  // We remember what is expanded, not what is collapsed: the reference list
  // opens on its projects, and sub-projects are asked for. A mission created
  // along the way therefore arrives collapsed, like the others.
  const [expanded, setExpanded] = useState<ReadonlySet<number>>(() => new Set());
  // An export reads the whole reference list again, then writes a file: long
  // enough for a second click to start a second one.
  const [exporting, setExporting] = useState(false);
  // A move the server turned away: the table shows the reference list as it
  // is, so the refusal has to be said in words.
  const [attachFailed, setAttachFailed] = useState(false);
  const mayWrite = useMayWrite();

  const toggle = useCallback((id: number) => {
    setExpanded((current) => {
      const next = new Set(current);
      if (!next.delete(id)) next.add(id);
      return next;
    });
  }, []);

  async function refresh() {
    await queryClient.invalidateQueries();
  }

  return {
    isLoading,
    isManager: holds(me?.role, "MANAGER"),
    /** Whether the person reading may change the reference list at all. */
    mayWrite,
    tree: buildProjectTree(kept, sorted),

    /** Missions kept, and missions the reference list carries in all. */
    visible: kept.length,
    total: missions.length,

    /** Whether a mission's sub-projects are showing. */
    isExpanded: (id: number) => expanded.has(id),
    toggle,

    /** Reads the reference list again after a change made in the panel. */
    refresh,

    async declare(label: string, kind: ProjectKind, parentId?: number) {
      const created = await createProject({
        label,
        kind,
        status: "exploration",
        ...(parentId ? { parent_id: parentId } : {}),
      });
      await refresh();
      return mutationResult<ProjectResponse>(created);
    },

    /** Whether the last move was refused, and the list read again as it is. */
    hasAttachError: attachFailed,

    /**
     * Makes a mission a work package of the project it was dropped onto.
     *
     * The screen never anticipates the move: a row that jumped under its new
     * project before the server agreed would have to jump back. The list is
     * read again once the answer is in, refused or not.
     */
    async attach(missionId: number, parentId: number) {
      setAttachFailed(false);
      try {
        await attachProject(missionId, { parent_id: parentId });
      } catch {
        setAttachFailed(true);
      }
      await refresh();
    },

    /** Whether an export is running: the button must not start a second one. */
    isExporting: exporting,

    /**
     * Writes the whole reference list to a workbook.
     *
     * The export ignores the filters and the archived switch: one exports a
     * reference list to work on it elsewhere, and a file missing the missions
     * the screen happened to be hiding would read as a complete one.
     */
    async exportToExcel() {
      setExporting(true);
      try {
        const response = await listProjects({ include_inactive: true });
        const all = mutationResult<ProjectListItemResponse[]>(response);
        const { downloadProjectsWorkbook } = await import("@/lib/projects-export");
        await downloadProjectsWorkbook(all, new Date());
      } finally {
        setExporting(false);
      }
    },

    async importCsv(content: string): Promise<ImportReportResponse> {
      const report = await importProjects({ rows: parseProjectsCsv(content) });
      await refresh();
      return mutationResult<ImportReportResponse>(report);
    },
  };
}

import type { ProjectListItemResponse } from "@/lib/api/generated/model";
import { NO_SORT, sortComparator, type MissionSort } from "@/lib/mission-sort";

/** A mission and, if it is a project, the work packages under it. */
export interface ProjectNode {
  mission: ProjectListItemResponse;
  lots: ProjectListItemResponse[];
}

const HORS_PROJET = "off_project";

/**
 * Arranges the reference list as a tree: each project followed by its packages.
 *
 * The sort applies to each level separately — projects among themselves, work
 * packages within their project: ordering the list must not tear a sub-project
 * away from its parent.
 *
 * A work package whose parent is absent from the list — filtered out, archived
 * — moves up to the first level rather than disappearing: an invisible mission
 * would be a mission believed deleted.
 */
export function buildProjectTree(
  missions: ProjectListItemResponse[],
  sorted: MissionSort = NO_SORT,
): ProjectNode[] {
  const ordre = sortComparator(sorted);
  const projets = missions.filter((m) => m.project.kind === "project");
  const lots = missions.filter((m) => m.project.kind === "work_package");
  const idsPresents = new Set(projets.map((m) => m.project.id));

  const noeuds: ProjectNode[] = [...projets].sort(ordre).map((mission) => ({
    mission,
    lots: lots.filter((l) => l.project.parent_id === mission.project.id).sort(ordre),
  }));

  const orphelins = lots
    .filter(
      (l) => l.project.parent_id === null || !idsPresents.has(l.project.parent_id),
    )
    .sort(ordre)
    .map((lot) => ({ mission: lot, lots: [] }));

  return [...noeuds, ...orphelins];
}

/** Activites hors projet, listees a part : elles n'ont ni lot ni estime. */
export function offProjectActivities(
  missions: ProjectListItemResponse[],
): ProjectListItemResponse[] {
  return missions
    .filter((m) => m.project.kind === HORS_PROJET)
    .sort(sortComparator(NO_SORT));
}

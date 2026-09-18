import type { ProjectListItemResponse } from "@/lib/api/generated/model";
import { NO_SORT, sortComparator, type MissionSort } from "@/lib/mission-sort";

/** A mission and, if it is a project, the work packages under it. */
export interface ProjectNode {
  mission: ProjectListItemResponse;
  workPackages: ProjectListItemResponse[];
}

const OFF_PROJECT = "off_project";

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
  const compare = sortComparator(sorted);
  const projects = missions.filter((m) => m.project.kind === "project");
  const workPackages = missions.filter((m) => m.project.kind === "work_package");
  const presentIds = new Set(projects.map((m) => m.project.id));

  const nodes: ProjectNode[] = [...projects].sort(compare).map((mission) => ({
    mission,
    workPackages: workPackages
      .filter((l) => l.project.parent_id === mission.project.id)
      .sort(compare),
  }));

  const orphans = workPackages
    .filter((l) => l.project.parent_id === null || !presentIds.has(l.project.parent_id))
    .sort(compare)
    .map((workPackage) => ({ mission: workPackage, workPackages: [] }));

  return [...nodes, ...orphans];
}

/** Off-project work, listed apart: it has neither package nor estimate. */
export function offProjectActivities(
  missions: ProjectListItemResponse[],
): ProjectListItemResponse[] {
  return missions
    .filter((m) => m.project.kind === OFF_PROJECT)
    .sort(sortComparator(NO_SORT));
}

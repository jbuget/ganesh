import type { ProjectResponse } from "@/lib/api/generated/model";

/** Missions proposables a l'ajout, reparties par nature. */
export interface AvailableMissions {
  projectMissions: ProjectResponse[];
  offProject: ProjectResponse[];
}

/**
 * Missions a user can still add to their grid.
 *
 * Those already there are ruled out: no two rows for the same mission. This
 * logic lives outside the component so it can be tested without depending on
 * how a menu renders.
 */
export function availableMissions(
  projects: ProjectResponse[],
  excludedIds: number[],
): AvailableMissions {
  const available = projects.filter((p) => !excludedIds.includes(p.id));
  return {
    projectMissions: available.filter((p) => p.kind !== "off_project"),
    offProject: available.filter((p) => p.kind === "off_project"),
  };
}

import type { ProjectResponse } from "@/lib/api/generated/model";

/** Missions proposables a l'ajout, reparties par nature. */
export interface AvailableMissions {
  projets: ProjectResponse[];
  horsProjet: ProjectResponse[];
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
  const disponibles = projects.filter((p) => !excludedIds.includes(p.id));
  return {
    projets: disponibles.filter((p) => p.kind !== "off_project"),
    horsProjet: disponibles.filter((p) => p.kind === "off_project"),
  };
}

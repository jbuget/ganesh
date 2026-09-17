import type { ProjectResponse } from "@/lib/api/generated/model";

/** Missions proposables a l'ajout, reparties par nature. */
export interface AvailableMissions {
  projets: ProjectResponse[];
  horsProjet: ProjectResponse[];
}

/**
 * Missions qu'un utilisateur peut encore ajouter a sa matrice.
 *
 * Celles deja presentes sont ecartees : on ne cree pas deux lignes pour la meme
 * mission. Cette logique vit hors du composant pour etre testable sans dependre
 * du rendu d'un menu.
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

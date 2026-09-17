import { arrayMove } from "@dnd-kit/sortable";

import type { BoardCardResponse, ProjectStatus } from "@/lib/api/generated/model";
import { PHASES } from "@/lib/board";
import type { Colonnes } from "@/lib/use-board";

/**
 * Deplacements de cartes sur le tableau, independamment du geste qui les
 * declenche.
 *
 * Le survol et le depot partagent ces calculs : ce qu'on voit pendant le
 * glissement est donc exactement ce qui sera enregistre.
 */

/** Phase et rang d'une carte, ou null si elle n'est pas sur le tableau. */
export function localiser(
  colonnes: Colonnes,
  projectId: number,
): { statut: ProjectStatus; position: number } | null {
  for (const { statut } of PHASES) {
    const position =
      colonnes[statut]?.findIndex((c) => c.project.id === projectId) ?? -1;
    if (position !== -1) return { statut, position };
  }
  return null;
}

/**
 * Rang qu'occuperait la carte glissee dans une phase.
 *
 * `apres` dit si le curseur a depasse la moitie de la carte survolee : on se
 * glisse alors derriere elle plutot que devant.
 */
export function indexVise(
  cartes: BoardCardResponse[],
  surId: number | null,
  apres: boolean,
): number {
  if (surId === null) return cartes.length;
  const index = cartes.findIndex((c) => c.project.id === surId);
  if (index === -1) return cartes.length;
  return apres ? index + 1 : index;
}

/**
 * Fait passer une carte dans une autre phase.
 *
 * Rend null si le deplacement n'a pas lieu d'etre : le survol appelle cette
 * fonction a chaque mouvement de souris, et reecrire un etat identique ferait
 * clignoter le tableau.
 */
export function changerDeColonne(
  colonnes: Colonnes,
  projectId: number,
  vers: ProjectStatus,
  index: number,
): Colonnes | null {
  const depart = localiser(colonnes, projectId);
  if (!depart || depart.statut === vers) return null;

  const carte = colonnes[depart.statut][depart.position];
  const arrivee = colonnes[vers];
  const rang = Math.max(0, Math.min(index, arrivee.length));

  return {
    ...colonnes,
    [depart.statut]: colonnes[depart.statut].filter((c) => c.project.id !== projectId),
    [vers]: [...arrivee.slice(0, rang), carte, ...arrivee.slice(rang)],
  };
}

/** Change le rang d'une carte au sein de sa phase. Null si elle ne bouge pas. */
export function reordonner(
  colonnes: Colonnes,
  projectId: number,
  index: number,
): Colonnes | null {
  const place = localiser(colonnes, projectId);
  if (!place) return null;

  const cartes = colonnes[place.statut];
  const rang = Math.max(0, Math.min(index, cartes.length - 1));
  if (rang === place.position) return null;

  return { ...colonnes, [place.statut]: arrayMove(cartes, place.position, rang) };
}

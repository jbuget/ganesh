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
export function locate(
  columns: Colonnes,
  projectId: number,
): { status: ProjectStatus; position: number } | null {
  for (const { status } of PHASES) {
    const position =
      columns[status]?.findIndex((c) => c.project.id === projectId) ?? -1;
    if (position !== -1) return { status, position };
  }
  return null;
}

/**
 * Rang qu'occuperait la carte glissee dans une phase.
 *
 * `apres` dit si le curseur a depasse la moitie de la carte survolee : on se
 * glisse alors derriere elle plutot que devant.
 */
export function targetIndex(
  cards: BoardCardResponse[],
  overId: number | null,
  apres: boolean,
): number {
  if (overId === null) return cards.length;
  const index = cards.findIndex((c) => c.project.id === overId);
  if (index === -1) return cards.length;
  return apres ? index + 1 : index;
}

/**
 * Fait passer une carte dans une autre phase.
 *
 * Rend null si le deplacement n'a pas lieu d'etre : le survol appelle cette
 * fonction a chaque mouvement de souris, et reecrire un etat identique ferait
 * clignoter le tableau.
 */
export function moveToColumn(
  columns: Colonnes,
  projectId: number,
  vers: ProjectStatus,
  index: number,
): Colonnes | null {
  const depart = locate(columns, projectId);
  if (!depart || depart.status === vers) return null;

  const card = columns[depart.status][depart.position];
  const arrivee = columns[vers];
  const rang = Math.max(0, Math.min(index, arrivee.length));

  return {
    ...columns,
    [depart.status]: columns[depart.status].filter((c) => c.project.id !== projectId),
    [vers]: [...arrivee.slice(0, rang), card, ...arrivee.slice(rang)],
  };
}

/** Change le rang d'une carte au sein de sa phase. Null si elle ne bouge pas. */
export function reorder(
  columns: Colonnes,
  projectId: number,
  index: number,
): Colonnes | null {
  const place = locate(columns, projectId);
  if (!place) return null;

  const cards = columns[place.status];
  const rang = Math.max(0, Math.min(index, cards.length - 1));
  if (rang === place.position) return null;

  return { ...columns, [place.status]: arrayMove(cards, place.position, rang) };
}

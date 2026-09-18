import { arrayMove } from "@dnd-kit/sortable";

import type { BoardCardResponse, ProjectStatus } from "@/lib/api/generated/model";
import { PHASES } from "@/lib/board";
import type { Columns } from "@/lib/use-board";

/**
 * Card moves on the board, independent of the gesture that triggers them.
 *
 * Hovering and dropping share these computations: what one sees during the
 * drag is therefore exactly what will be saved.
 */

/** Phase and rank of a card, or null if it is not on the board. */
export function locate(
  columns: Columns,
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
 * The rank the dragged card would take within a phase.
 *
 * `after` says whether the cursor went past the middle of the hovered card: it
 * then slips behind it rather than in front.
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
 * Moves a card into another phase.
 *
 * Returns null when the move has no reason to happen: hovering calls this
 * function on every mouse move, and rewriting an identical state would make
 * the board flicker.
 */
export function moveToColumn(
  columns: Columns,
  projectId: number,
  vers: ProjectStatus,
  index: number,
): Columns | null {
  const origin = locate(columns, projectId);
  if (!origin || origin.status === vers) return null;

  const card = columns[origin.status][origin.position];
  const destination = columns[vers];
  const rang = Math.max(0, Math.min(index, destination.length));

  return {
    ...columns,
    [origin.status]: columns[origin.status].filter((c) => c.project.id !== projectId),
    [vers]: [...destination.slice(0, rang), card, ...destination.slice(rang)],
  };
}

/** Changes a card's rank within its phase. Null if it does not move. */
export function reorder(
  columns: Columns,
  projectId: number,
  index: number,
): Columns | null {
  const location = locate(columns, projectId);
  if (!location) return null;

  const cards = columns[location.status];
  const rang = Math.max(0, Math.min(index, cards.length - 1));
  if (rang === location.position) return null;

  return { ...columns, [location.status]: arrayMove(cards, location.position, rang) };
}

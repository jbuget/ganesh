"use client";

import type { DragEndEvent, DragOverEvent, DragStartEvent } from "@dnd-kit/core";
import { useRef, useState } from "react";

import type { BoardCardResponse } from "@/lib/api/generated/model";
import { PHASES } from "@/lib/board";
import { moveToColumn, targetIndex, locate, reorder } from "@/lib/board-move";
import type { Colonnes, useBoard } from "@/lib/use-board";

/**
 * Dragging a card, from the first hover to the save.
 *
 * A gesture is a transaction: the starting state is kept so it can be returned
 * to, and the live state is reworked on every hover then displayed. Columns
 * therefore open and close under the cursor, and dropping only confirms what
 * one already saw.
 *
 * The live state is held in a ref, not read from the render: between two
 * hovers, React has not necessarily replayed the component.
 */
export function useBoardDrag(board: ReturnType<typeof useBoard>) {
  const [isDragging, setEnDeplacement] = useState<BoardCardResponse | null>(null);
  const gesture = useRef<{ depart: Colonnes; alive: Colonnes } | null>(null);

  function apply(next_ones: Colonnes) {
    gesture.current!.alive = next_ones;
    board.preview(next_ones);
  }

  /** The phase aimed at: one hovers either a column or a card. */
  function targetColumn(columns: Colonnes, overId: string | number) {
    const phase = PHASES.find(({ status }) => status === overId);
    if (phase) return phase.status;
    return locate(columns, Number(overId))?.status ?? null;
  }

  /** The id of the hovered card, or null when it is a column's background. */
  const hoveredCard = (overId: string | number) =>
    typeof overId === "number" ? overId : null;

  /** Le curseur a-t-il depasse le milieu de la carte survolee ? */
  function pastHalfway(event: DragOverEvent | DragEndEvent) {
    const glissee = event.active.rect.current.translated;
    const survolee = event.over?.rect;
    if (!glissee || !survolee) return false;
    return glissee.top > survolee.top + survolee.height / 2;
  }

  return {
    isDragging,

    onDragStart(event: DragStartEvent) {
      if (!board.columns) return;
      const id = Number(event.active.id);
      const place = locate(board.columns, id);
      if (!place) return;
      gesture.current = { depart: board.columns, alive: board.columns };
      setEnDeplacement(board.columns[place.status][place.position]);
    },

    onDragOver(event: DragOverEvent) {
      if (!gesture.current || !event.over) return;
      const { alive } = gesture.current;
      const id = Number(event.active.id);

      const target = targetColumn(alive, event.over.id);
      if (!target) return;

      const overId = hoveredCard(event.over.id);
      const index = targetIndex(alive[target], overId, pastHalfway(event));

      const change = moveToColumn(alive, id, target, index);
      if (change) {
        apply(change);
        return;
      }

      // Already in the right phase: the rank goes on following the cursor,
      // otherwise the slot would stay frozen where one entered the column.
      if (overId === null || overId === id) return;
      const vise = locate(alive, overId);
      if (!vise) return;
      const sorted = reorder(alive, id, vise.position);
      if (sorted) apply(sorted);
    },

    async onDragEnd(event: DragEndEvent) {
      setEnDeplacement(null);
      const encours = gesture.current;
      gesture.current = null;
      if (!encours) return;

      const id = Number(event.active.id);
      const depart = locate(encours.depart, id);
      if (!depart) return;

      // Nothing to recompute: hovering has already placed the card, and the
      // dotted slot showed exactly where it would land. Dropping confirms what
      // one was looking at.
      const finales = encours.alive;
      const arrivee = locate(finales, id);
      if (!arrivee) return;
      if (arrivee.status === depart.status && arrivee.position === depart.position) {
        // Nothing moved: the screen goes back as it was, with no server call.
        board.preview(encours.depart);
        return;
      }

      await board.move(id, arrivee.status, arrivee.position, finales);
    },

    onDragCancel() {
      setEnDeplacement(null);
      if (gesture.current) board.preview(gesture.current.depart);
      gesture.current = null;
    },
  };
}

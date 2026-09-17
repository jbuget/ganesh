"use client";

import type { DragEndEvent, DragOverEvent, DragStartEvent } from "@dnd-kit/core";
import { useRef, useState } from "react";

import type { BoardCardResponse } from "@/lib/api/generated/model";
import { PHASES } from "@/lib/board";
import { moveToColumn, targetIndex, locate, reorder } from "@/lib/board-move";
import type { Colonnes, useBoard } from "@/lib/use-board";

/**
 * Le glissement d'une carte, du premier survol jusqu'a l'enregistrement.
 *
 * Un geste est une transaction : on garde l'etat de depart pour pouvoir y
 * revenir, et l'etat vivant est remanie a chaque survol puis affiche. Les
 * colonnes s'ouvrent et se referment donc sous le curseur, et le depot ne fait
 * qu'entériner ce que l'on voyait deja.
 *
 * L'etat vivant est tenu dans une ref, et non lu depuis le rendu : entre deux
 * survols, React n'a pas forcement rejoue le composant.
 */
export function useBoardDrag(board: ReturnType<typeof useBoard>) {
  const [isDragging, setEnDeplacement] = useState<BoardCardResponse | null>(null);
  const gesture = useRef<{ depart: Colonnes; alive: Colonnes } | null>(null);

  function apply(next_ones: Colonnes) {
    gesture.current!.alive = next_ones;
    board.preview(next_ones);
  }

  /** La phase visee : on survole soit une colonne, soit une carte. */
  function targetColumn(columns: Colonnes, overId: string | number) {
    const phase = PHASES.find(({ status }) => status === overId);
    if (phase) return phase.status;
    return locate(columns, Number(overId))?.status ?? null;
  }

  /** L'id de la carte survolee, ou null si c'est le fond d'une colonne. */
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

      // Deja dans la bonne phase : le rang continue de suivre le curseur, sinon
      // l'emplacement resterait fige la ou l'on est entre dans la colonne.
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

      // Rien a recalculer : le survol a deja place la carte, et l'emplacement
      // en pointilles montrait exactement ou elle allait tomber. Deposer, c'est
      // enteriner ce que l'on voyait.
      const finales = encours.alive;
      const arrivee = locate(finales, id);
      if (!arrivee) return;
      if (arrivee.status === depart.status && arrivee.position === depart.position) {
        // Rien n'a bouge : on remet l'ecran tel qu'il etait, sans appel serveur.
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

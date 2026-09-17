"use client";

import type { DragEndEvent, DragOverEvent, DragStartEvent } from "@dnd-kit/core";
import { useRef, useState } from "react";

import type { BoardCardResponse } from "@/lib/api/generated/model";
import { PHASES } from "@/lib/board";
import { changerDeColonne, indexVise, localiser, reordonner } from "@/lib/board-move";
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
  const [enDeplacement, setEnDeplacement] = useState<BoardCardResponse | null>(null);
  const geste = useRef<{ depart: Colonnes; vivant: Colonnes } | null>(null);

  function appliquer(suivantes: Colonnes) {
    geste.current!.vivant = suivantes;
    board.previsualiser(suivantes);
  }

  /** La phase visee : on survole soit une colonne, soit une carte. */
  function colonneCible(colonnes: Colonnes, overId: string | number) {
    const phase = PHASES.find(({ statut }) => statut === overId);
    if (phase) return phase.statut;
    return localiser(colonnes, Number(overId))?.statut ?? null;
  }

  /** L'id de la carte survolee, ou null si c'est le fond d'une colonne. */
  const carteSurvolee = (overId: string | number) =>
    typeof overId === "number" ? overId : null;

  /** Le curseur a-t-il depasse le milieu de la carte survolee ? */
  function depasseLaMoitie(event: DragOverEvent | DragEndEvent) {
    const glissee = event.active.rect.current.translated;
    const survolee = event.over?.rect;
    if (!glissee || !survolee) return false;
    return glissee.top > survolee.top + survolee.height / 2;
  }

  return {
    enDeplacement,

    onDragStart(event: DragStartEvent) {
      if (!board.colonnes) return;
      const id = Number(event.active.id);
      const place = localiser(board.colonnes, id);
      if (!place) return;
      geste.current = { depart: board.colonnes, vivant: board.colonnes };
      setEnDeplacement(board.colonnes[place.statut][place.position]);
    },

    onDragOver(event: DragOverEvent) {
      if (!geste.current || !event.over) return;
      const { vivant } = geste.current;
      const id = Number(event.active.id);

      const cible = colonneCible(vivant, event.over.id);
      if (!cible) return;

      const surId = carteSurvolee(event.over.id);
      const index = indexVise(vivant[cible], surId, depasseLaMoitie(event));

      const changement = changerDeColonne(vivant, id, cible, index);
      if (changement) {
        appliquer(changement);
        return;
      }

      // Deja dans la bonne phase : le rang continue de suivre le curseur, sinon
      // l'emplacement resterait fige la ou l'on est entre dans la colonne.
      if (surId === null || surId === id) return;
      const vise = localiser(vivant, surId);
      if (!vise) return;
      const tri = reordonner(vivant, id, vise.position);
      if (tri) appliquer(tri);
    },

    async onDragEnd(event: DragEndEvent) {
      setEnDeplacement(null);
      const encours = geste.current;
      geste.current = null;
      if (!encours) return;

      const id = Number(event.active.id);
      const depart = localiser(encours.depart, id);
      if (!depart) return;

      // Rien a recalculer : le survol a deja place la carte, et l'emplacement
      // en pointilles montrait exactement ou elle allait tomber. Deposer, c'est
      // enteriner ce que l'on voyait.
      const finales = encours.vivant;
      const arrivee = localiser(finales, id);
      if (!arrivee) return;
      if (arrivee.statut === depart.statut && arrivee.position === depart.position) {
        // Rien n'a bouge : on remet l'ecran tel qu'il etait, sans appel serveur.
        board.previsualiser(encours.depart);
        return;
      }

      await board.deplacer(id, arrivee.statut, arrivee.position, finales);
    },

    onDragCancel() {
      setEnDeplacement(null);
      if (geste.current) board.previsualiser(geste.current.depart);
      geste.current = null;
    },
  };
}

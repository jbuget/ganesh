"use client";

import {
  DndContext,
  DragOverlay,
  PointerSensor,
  KeyboardSensor,
  closestCorners,
  pointerWithin,
  rectIntersection,
  useSensor,
  useSensors,
  type CollisionDetection,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { arrayMove, sortableKeyboardCoordinates } from "@dnd-kit/sortable";
import { useState } from "react";

import { BoardColumn } from "@/components/molecules/BoardColumn";
import { ProjectCard } from "@/components/molecules/ProjectCard";
import type { BoardCardResponse, ProjectStatus } from "@/lib/api/generated/model";
import { PHASES } from "@/lib/board";
import { useBoard, type Colonnes } from "@/lib/use-board";

/**
 * Ce qui se trouve reellement sous le curseur, en priorite.
 *
 * `closestCorners` seul visait la carte voisine plutot que la colonne survolee :
 * deposer dans une colonne vide envoyait la carte dans la colonne d'a cote.
 */
const detectionDeCollision: CollisionDetection = (args) => {
  const sousLeCurseur = pointerWithin(args);
  if (sousLeCurseur.length > 0) return sousLeCurseur;

  const recouvrement = rectIntersection(args);
  return recouvrement.length > 0 ? recouvrement : closestCorners(args);
};

/** Retrouve la colonne qui contient une carte. */
function colonneDe(colonnes: Colonnes, projectId: number): ProjectStatus | null {
  for (const { statut } of PHASES) {
    if (colonnes[statut]?.some((c) => c.project.id === projectId)) return statut;
  }
  return null;
}

/** Tableau de bord des projets, une colonne par phase. */
export function BoardPage() {
  const board = useBoard();
  const [enDeplacement, setEnDeplacement] = useState<BoardCardResponse | null>(null);

  const sensors = useSensors(
    // Quelques pixels avant de saisir : sans cela, un simple clic ferait
    // demarrer un glissement.
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  );

  function handleDragStart(event: DragStartEvent) {
    const id = Number(event.active.id);
    const depart = board.colonnes && colonneDe(board.colonnes, id);
    setEnDeplacement(
      depart
        ? (board.colonnes?.[depart].find((c) => c.project.id === id) ?? null)
        : null,
    );
  }

  async function handleDragEnd(event: DragEndEvent) {
    setEnDeplacement(null);
    const { active, over } = event;
    if (!over || !board.colonnes) return;

    const id = Number(active.id);
    const depart = colonneDe(board.colonnes, id);
    if (!depart) return;

    // On peut relacher sur une colonne vide comme sur une autre carte.
    const arrivee =
      (PHASES.find((p) => p.statut === over.id)?.statut as ProjectStatus) ??
      colonneDe(board.colonnes, Number(over.id));
    if (!arrivee) return;

    const cartesDepart = board.colonnes[depart];
    const carte = cartesDepart.find((c) => c.project.id === id);
    if (!carte) return;

    const cartesArrivee = depart === arrivee ? cartesDepart : board.colonnes[arrivee];
    const indexSurvole = cartesArrivee.findIndex(
      (c) => c.project.id === Number(over.id),
    );

    const suivantes: Colonnes = { ...board.colonnes };
    let rang: number;

    if (depart === arrivee) {
      const depuis = cartesDepart.findIndex((c) => c.project.id === id);
      rang = indexSurvole === -1 ? cartesDepart.length - 1 : indexSurvole;
      if (depuis === rang) return;
      suivantes[arrivee] = arrayMove(cartesDepart, depuis, rang);
    } else {
      rang = indexSurvole === -1 ? cartesArrivee.length : indexSurvole;
      suivantes[depart] = cartesDepart.filter((c) => c.project.id !== id);
      suivantes[arrivee] = [
        ...cartesArrivee.slice(0, rang),
        carte,
        ...cartesArrivee.slice(rang),
      ];
    }

    await board.deplacer(id, arrivee, rang, suivantes);
  }

  return (
    <main className="mx-auto max-w-[1600px] p-6">
      <header className="mb-6">
        <h1 className="text-lg font-semibold">Tableau de bord</h1>
        <p className="text-sm text-slate-500">
          Glissez une mission pour changer sa phase ou la réordonner. L&apos;ordre
          choisi est conservé.
        </p>
      </header>

      {board.enErreur && (
        <p className="mb-4 rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-900">
          Le déplacement n&apos;a pas pu être enregistré. Le tableau a été rechargé.
        </p>
      )}

      {!board.colonnes ? (
        <p className="text-sm text-slate-500">Chargement…</p>
      ) : (
        <DndContext
          sensors={sensors}
          collisionDetection={detectionDeCollision}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
          onDragCancel={() => setEnDeplacement(null)}
        >
          <div className="flex gap-4 overflow-x-auto pb-4">
            {PHASES.map(({ statut }) => (
              <BoardColumn
                key={statut}
                statut={statut}
                cartes={board.colonnes?.[statut] ?? []}
              />
            ))}
          </div>

          {/*
            La copie qui suit le curseur, legerement inclinee et soulevee.

            Aucune animation de retour : elle vise l'element d'origine, qui a
            change de place ou de colonne entre-temps, et laissait alors une
            carte fantome affichee en permanence.
          */}
          <DragOverlay dropAnimation={null}>
            {enDeplacement && (
              <div className="w-64 rotate-2 scale-[1.02] cursor-grabbing">
                <ProjectCard carte={enDeplacement} enDeplacement />
              </div>
            )}
          </DragOverlay>
        </DndContext>
      )}
    </main>
  );
}

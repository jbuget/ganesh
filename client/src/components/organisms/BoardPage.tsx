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
  type Collision,
  type CollisionDetection,
} from "@dnd-kit/core";
import { sortableKeyboardCoordinates } from "@dnd-kit/sortable";

import { PageHeader } from "@/components/atoms/PageHeader";
import { BoardColumn } from "@/components/molecules/BoardColumn";
import { BoardFilters } from "@/components/molecules/BoardFilters";
import { ProjectPanel } from "@/components/organisms/ProjectPanel";
import { ProjectCard } from "@/components/molecules/ProjectCard";
import { PHASES } from "@/lib/board";
import { filtrerCartes } from "@/lib/board-filters";
import { useBoard } from "@/lib/use-board";
import { useBoardDrag } from "@/lib/use-board-drag";
import { useBoardFilters } from "@/lib/use-board-filters";
import { useMissionOuverte } from "@/lib/mission-ouverte";

/**
 * Une carte survolee l'emporte sur la colonne qui la contient.
 *
 * Les deux se trouvent sous le curseur, et la colonne seule ne dit que la phase
 * d'arrivee : sans cette preference, toute carte tombait en bas de colonne,
 * quel que soit l'endroit vise.
 */
const prioriserLesCartes = (collisions: Collision[]) => {
  const cartes = collisions.filter(({ id }) => typeof id === "number");
  return cartes.length > 0 ? cartes : collisions;
};

/**
 * Ce qui se trouve reellement sous le curseur, en priorite.
 *
 * `closestCorners` seul visait la carte voisine plutot que la colonne survolee :
 * deposer dans une colonne vide envoyait la carte dans la colonne d'a cote.
 */
const detectionDeCollision: CollisionDetection = (args) => {
  const sousLeCurseur = pointerWithin(args);
  if (sousLeCurseur.length > 0) return prioriserLesCartes(sousLeCurseur);

  const recouvrement = rectIntersection(args);
  if (recouvrement.length > 0) return prioriserLesCartes(recouvrement);
  return closestCorners(args);
};

/** Kanban des missions, une colonne par phase. */
export function BoardPage() {
  const board = useBoard();
  const glissement = useBoardDrag(board);
  const { filtres, actif, definir, effacer } = useBoardFilters();

  // La mission ouverte vit dans l'URL : un panneau se partage par un lien, et
  // le retour arriere le referme, comme on s'y attend d'un ecran a part.
  const panneau = useMissionOuverte();

  // Les six phases restent affichees en toutes circonstances, meme vides : le
  // tableau garde sa forme d'un filtre a l'autre, et une colonne sans carte se
  // lit comme une reponse, pas comme une disparition.
  //
  // Les colonnes sont calculees une fois : le decompte de la barre et celui de
  // chaque colonne doivent parler des memes cartes.
  const colonnesAffichees = PHASES.map(({ statut }) => ({
    statut,
    cartes: filtrerCartes(board.colonnes?.[statut] ?? [], filtres),
  }));

  const visibles = colonnesAffichees.reduce((total, c) => total + c.cartes.length, 0);
  const total = PHASES.reduce(
    (somme, { statut }) => somme + (board.colonnes?.[statut]?.length ?? 0),
    0,
  );

  const sensors = useSensors(
    // Quelques pixels avant de saisir : sans cela, un simple clic ferait
    // demarrer un glissement.
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  );

  // Le tableau prend toute la largeur, contrairement aux autres ecrans : six
  // colonnes cote a cote y gagnent chaque pixel, et une marge centree les
  // etranglerait sans rien apporter a la lecture.
  return (
    <main className="p-6">
      <PageHeader
        titre="Kanban"
        soustitre={
          // Sous filtre, la liste affichee n'est plus la liste rangee : un
          // depot y viserait un rang qui n'existe pas. Les cartes se figent
          // donc, et l'entete dit pourquoi plutot que de laisser chercher.
          actif
            ? "Tableau filtré : les cartes ne se déplacent plus. Effacez les filtres pour les réorganiser."
            : "Glissez une mission pour changer sa phase ou la réordonner. L'ordre choisi est conservé."
        }
      />

      <BoardFilters
        filtres={filtres}
        actif={actif}
        onChange={definir}
        onEffacer={effacer}
        visibles={visibles}
        total={total}
      />

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
          onDragStart={glissement.onDragStart}
          onDragOver={glissement.onDragOver}
          onDragEnd={glissement.onDragEnd}
          onDragCancel={glissement.onDragCancel}
        >
          <div className="flex gap-4 overflow-x-auto pb-4">
            {colonnesAffichees.map(({ statut, cartes }) => (
              <BoardColumn
                key={statut}
                statut={statut}
                cartes={cartes}
                onIntervenantsChange={board.recharger}
                onOpen={panneau.ouvrir}
                figees={actif}
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
            {glissement.enDeplacement && (
              <div className="w-64 rotate-2 scale-[1.02] cursor-grabbing">
                <ProjectCard carte={glissement.enDeplacement} enDeplacement />
              </div>
            )}
          </DragOverlay>
        </DndContext>
      )}

      {panneau.missionOuverte && (
        <ProjectPanel
          key={panneau.missionOuverte}
          projectId={panneau.missionOuverte}
          onClose={panneau.fermer}
          onMissionChanged={board.recharger}
        />
      )}
    </main>
  );
}

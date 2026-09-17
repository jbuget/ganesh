"use client";

import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";

import { SortableProjectCard } from "@/components/molecules/SortableProjectCard";
import type { BoardCardResponse, ProjectStatus } from "@/lib/api/generated/model";
import { libellePhase, pastillePhase } from "@/lib/board";

interface BoardColumnProps {
  statut: ProjectStatus;
  cartes: BoardCardResponse[];
  onIntervenantsChange?: () => void | Promise<void>;
  onOpen?: (projectId: number) => void;
}

/**
 * Une phase et ses cartes, zone de depot du glisser-deposer.
 *
 * Le titre et les cartes tiennent dans un meme bloc : une colonne se lit alors
 * comme une unite, et non comme un intitule flottant au-dessus d'une liste.
 */
export function BoardColumn({
  statut,
  cartes,
  onIntervenantsChange,
  onOpen,
}: BoardColumnProps) {
  const { setNodeRef, isOver } = useDroppable({ id: statut });

  return (
    <section
      aria-label={libellePhase(statut)}
      // Les six phases se partagent la largeur disponible plutot que d'imposer
      // un defilement des qu'un ecran n'atteint pas 1600 px. En deca de la
      // largeur minimale, le conteneur reprend le defilement horizontal.
      className={[
        // Une bordure, et non un `ring` : celui-ci se dessine hors de la boite,
        // et le conteneur de defilement rognait alors le bord gauche de la
        // premiere colonne et le bord droit de la derniere.
        "flex min-w-60 max-w-80 flex-1 flex-col rounded-xl border transition-colors",
        isOver ? "border-sky-300 bg-sky-50" : "border-slate-300 bg-slate-100",
      ].join(" ")}
    >
      <header className="flex items-center justify-between gap-2 px-3 pt-3 pb-2">
        <h2 className="flex items-center gap-2 text-sm font-medium text-slate-700">
          <span
            aria-hidden
            className={`size-2.5 shrink-0 rounded-full ${pastillePhase(statut)}`}
          />
          {libellePhase(statut)}
        </h2>
        <span className="text-xs tabular-nums text-slate-400">{cartes.length}</span>
      </header>

      <ul ref={setNodeRef} className="flex min-h-32 flex-1 flex-col gap-2 px-2 pb-2">
        <SortableContext
          items={cartes.map((carte) => carte.project.id)}
          strategy={verticalListSortingStrategy}
        >
          {cartes.map((carte) => (
            <SortableProjectCard
              key={carte.project.id}
              carte={carte}
              onIntervenantsChange={onIntervenantsChange}
              onOpen={onOpen}
            />
          ))}
        </SortableContext>

        {/* Un <ul> n'admet que des <li> : un <p> nu casserait l'hydratation. */}
        {cartes.length === 0 && (
          <li className="px-1 py-6 text-center text-xs text-slate-400">
            Aucune mission
          </li>
        )}
      </ul>
    </section>
  );
}

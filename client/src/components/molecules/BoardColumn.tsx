"use client";

import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";

import { SortableProjectCard } from "@/components/molecules/SortableProjectCard";
import type { BoardCardResponse, ProjectStatus } from "@/lib/api/generated/model";
import { libellePhase } from "@/lib/board";

interface BoardColumnProps {
  statut: ProjectStatus;
  cartes: BoardCardResponse[];
}

/** Une phase et ses cartes, zone de depot du glisser-deposer. */
export function BoardColumn({ statut, cartes }: BoardColumnProps) {
  const { setNodeRef, isOver } = useDroppable({ id: statut });

  return (
    <section aria-label={libellePhase(statut)} className="flex w-64 shrink-0 flex-col">
      <header className="mb-2 flex items-baseline justify-between px-1">
        <h2 className="text-sm font-medium text-slate-700">{libellePhase(statut)}</h2>
        <span className="text-xs tabular-nums text-slate-400">{cartes.length}</span>
      </header>

      <ul
        ref={setNodeRef}
        className={[
          "flex min-h-32 flex-1 flex-col gap-2 rounded-lg border border-dashed p-2 transition-colors",
          isOver ? "border-sky-400 bg-sky-50" : "border-slate-200 bg-slate-50/60",
        ].join(" ")}
      >
        <SortableContext
          items={cartes.map((carte) => carte.project.id)}
          strategy={verticalListSortingStrategy}
        >
          {cartes.map((carte) => (
            <SortableProjectCard key={carte.project.id} carte={carte} />
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

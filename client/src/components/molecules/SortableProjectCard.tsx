"use client";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical } from "lucide-react";

import { ProjectCard } from "@/components/molecules/ProjectCard";
import type { BoardCardResponse } from "@/lib/api/generated/model";

interface SortableProjectCardProps {
  carte: BoardCardResponse;
  onIntervenantsChange?: () => void | Promise<void>;
  onOpen?: (projectId: number) => void;
  /** Le tableau est filtre : la carte se lit et s'ouvre, mais ne se range plus. */
  figee?: boolean;
}

/**
 * Carte deplacable.
 *
 * Pendant le glissement, la carte cede la place a un emplacement en pointilles
 * qui montre ou elle tombera : c'est la copie sous le curseur qui la represente.
 */
export function SortableProjectCard({
  carte,
  onIntervenantsChange,
  onOpen,
  figee,
}: SortableProjectCardProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: carte.project.id, disabled: figee });

  return (
    <li
      ref={setNodeRef}
      style={{ transform: CSS.Translate.toString(transform), transition }}
      // Un contour plutot qu'une bordure : il se superpose a la carte sans
      // rien ajouter a sa hauteur, donc l'emplacement fait exactement la
      // taille de la carte qui viendra s'y loger.
      className={
        isDragging
          ? "rounded-lg bg-sky-50/70 outline-2 -outline-offset-2 outline-dashed outline-sky-400"
          : undefined
      }
    >
      {/* Masquee, mais toujours mesuree : c'est elle qui donne sa hauteur a l'emplacement. */}
      <div className={isDragging ? "invisible" : undefined}>
        <ProjectCard
          carte={carte}
          onIntervenantsChange={onIntervenantsChange}
          onOpen={onOpen}
          poignee={
            figee ? null : (
              <button
                type="button"
                aria-label={`Déplacer ${carte.project.label}`}
                className="cursor-grab touch-none rounded p-0.5 text-slate-300 transition-colors hover:text-slate-500 active:cursor-grabbing"
                {...attributes}
                {...listeners}
              >
                <GripVertical className="size-4" />
              </button>
            )
          }
        />
      </div>
    </li>
  );
}

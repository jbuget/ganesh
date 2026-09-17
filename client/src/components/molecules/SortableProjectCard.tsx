"use client";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical } from "lucide-react";

import { ProjectCard } from "@/components/molecules/ProjectCard";
import type { BoardCardResponse } from "@/lib/api/generated/model";

interface SortableProjectCardProps {
  carte: BoardCardResponse;
}

/**
 * Carte deplacable.
 *
 * La carte d'origine reste en place, estompee, pendant que la copie suit le
 * curseur : on garde ainsi le repere de l'endroit d'ou l'on vient.
 */
export function SortableProjectCard({ carte }: SortableProjectCardProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: carte.project.id });

  return (
    <li
      ref={setNodeRef}
      style={{ transform: CSS.Translate.toString(transform), transition }}
      className={isDragging ? "opacity-40" : undefined}
    >
      <ProjectCard
        carte={carte}
        poignee={
          <button
            type="button"
            aria-label={`Déplacer ${carte.project.label}`}
            className="cursor-grab touch-none rounded p-0.5 text-slate-300 transition-colors hover:text-slate-500 active:cursor-grabbing"
            {...attributes}
            {...listeners}
          >
            <GripVertical className="size-4" />
          </button>
        }
      />
    </li>
  );
}

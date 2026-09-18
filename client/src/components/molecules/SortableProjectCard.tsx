"use client";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical } from "lucide-react";

import { ProjectCard } from "@/components/molecules/ProjectCard";
import type { BoardCardResponse } from "@/lib/api/generated/model";

interface SortableProjectCardProps {
  card: BoardCardResponse;
  /** Freezes the reference time: without it, server and client would diverge. */
  maintenant: Date;
  onIntervenantsChange?: () => void | Promise<void>;
  onOpen?: (projectId: number) => void;
  /** The board is filtered: the card reads and opens, but no longer arranges. */
  frozen?: boolean;
}

/**
 * A movable card.
 *
 * During the drag, the card gives way to a dotted slot showing where it will
 * land: it is the copy under the cursor that stands for it.
 */
export function SortableProjectCard({
  card,
  maintenant,
  onIntervenantsChange,
  onOpen,
  frozen,
}: SortableProjectCardProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: card.project.id, disabled: frozen });

  return (
    <li
      ref={setNodeRef}
      style={{ transform: CSS.Translate.toString(transform), transition }}
      // An outline rather than a border: it overlays the card without adding to
      // its height, so the slot is exactly the size of the card that will come
      // to sit in it.
      className={
        isDragging
          ? "rounded-lg bg-sky-50/70 outline-2 -outline-offset-2 outline-dashed outline-sky-400"
          : undefined
      }
    >
      {/* Hidden, but still measured: it is what gives the slot its height. */}
      <div className={isDragging ? "invisible" : undefined}>
        <ProjectCard
          card={card}
          maintenant={maintenant}
          onIntervenantsChange={onIntervenantsChange}
          onOpen={onOpen}
          handle={
            frozen ? null : (
              <button
                type="button"
                aria-label={`Déplacer ${card.project.label}`}
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

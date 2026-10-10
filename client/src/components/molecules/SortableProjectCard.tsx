"use client";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

import { ProjectCard } from "@/components/molecules/ProjectCard";
import type { BoardCardResponse } from "@/lib/api/generated/model";

interface SortableProjectCardProps {
  card: BoardCardResponse;
  /** Freezes the reference time: without it, server and client would diverge. */
  now: Date;
  onContributorsChange?: () => void | Promise<void>;
  onOpen?: (projectId: number) => void;
  /** Opens the mission on its thread, with the composer ready. */
  onOpenThread?: (projectId: number) => void;
  /**
   * Raises or lowers the mark the team follows the mission by. Absent for a
   * reader who may not write.
   */
  onFollowChange?: (projectId: number, following: boolean) => void;
  /** The reader may not write: the card reads and opens, but does not move. */
  frozen?: boolean;
}

/**
 * A movable card, grabbed anywhere.
 *
 * The whole card is what the eye aims at, so it is what the hand takes: a grip
 * a few pixels wide in a corner read as a board that would not move. A click
 * still opens the mission — the board only grabs once the pointer has
 * travelled a few pixels — and the click that ends a drop opens nothing:
 * @dnd-kit swallows it, holding a capturing listener a moment past the release.
 *
 * The keyboard keeps a handle of its own, unseen until it holds the focus: the
 * title, the avatars and the bubble all answer Enter, and a whole card
 * listening for it would move where one meant to open.
 *
 * During the drag, the card gives way to a dotted slot showing where it will
 * land: it is the copy under the cursor that stands for it.
 */
export function SortableProjectCard({
  card,
  now,
  onContributorsChange,
  onOpen,
  onOpenThread,
  onFollowChange,
  frozen,
}: SortableProjectCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    setActivatorNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: card.project.id, disabled: frozen });

  return (
    <li
      ref={setNodeRef}
      style={{ transform: CSS.Translate.toString(transform), transition }}
      // An outline rather than a border: it overlays the card without adding to
      // its height, so the slot is exactly the size of the card that will come
      // to sit in it.
      className={[
        "rounded-lg",
        isDragging
          ? "bg-sky-50/70 outline-2 -outline-offset-2 outline-dashed outline-sky-400"
          : // The handle is unseen: the card shows where the focus stands.
            "has-[[data-drag-handle]:focus-visible]:outline-2 has-[[data-drag-handle]:focus-visible]:outline-sky-500",
      ].join(" ")}
    >
      {/* Hidden, but still measured: it is what gives the slot its height. */}
      <div
        className={isDragging ? "invisible" : undefined}
        // The keyboard only ever starts from the handle: @dnd-kit ignores a key
        // pressed anywhere else, so Enter on the title still opens.
        {...listeners}
        onPointerDown={(event) => {
          // A popover the card opened is drawn elsewhere in the page but
          // still bubbles through it: pressing in it must not carry the card.
          if (!event.currentTarget.contains(event.target as Node)) return;
          listeners?.onPointerDown?.(event);
        }}
      >
        <ProjectCard
          card={card}
          now={now}
          onContributorsChange={onContributorsChange}
          onOpen={onOpen}
          onOpenThread={onOpenThread}
          onFollowChange={onFollowChange}
          handle={
            frozen ? null : (
              <button
                type="button"
                ref={setActivatorNodeRef}
                data-drag-handle
                aria-label={`Déplacer ${card.project.label}`}
                className="sr-only"
                {...attributes}
              />
            )
          }
        />
      </div>
    </li>
  );
}

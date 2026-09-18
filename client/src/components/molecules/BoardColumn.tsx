"use client";

import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";

import { SortableProjectCard } from "@/components/molecules/SortableProjectCard";
import type { BoardCardResponse, ProjectStatus } from "@/lib/api/generated/model";
import { phaseLabel, phaseDot } from "@/lib/board";

interface BoardColumnProps {
  status: ProjectStatus;
  cards: BoardCardResponse[];
  /** Freezes the reference time: without it, server and client would diverge. */
  maintenant: Date;
  onIntervenantsChange?: () => void | Promise<void>;
  onOpen?: (projectId: number) => void;
  /** The board is filtered: cards can be read, but no longer arranged. */
  frozen?: boolean;
}

/**
 * A phase and its cards, the drop zone of the drag and drop.
 *
 * Title and cards sit in one block: a column then reads as a unit, and not as
 * a heading floating above a list.
 *
 * The column takes the full height and it is its cards that scroll: a busy
 * phase no longer stretches the whole board, and every column's heading stays
 * level with the others.
 */
export function BoardColumn({
  status,
  cards,
  maintenant,
  onIntervenantsChange,
  onOpen,
  frozen,
}: BoardColumnProps) {
  const { setNodeRef, isOver } = useDroppable({ id: status });

  return (
    <section
      aria-label={phaseLabel(status)}
      // The six phases share the available width rather than forcing a scroll
      // as soon as a screen falls short of 1600 px. Below the minimum width,
      // the container takes horizontal scrolling back.
      className={[
        // A border, not a `ring`: a ring draws outside the box, and the
        // scrolling container then clipped the left edge of the first column
        // and the right edge of the last.
        "flex h-full min-w-72 max-w-96 flex-1 flex-col rounded-xl border transition-colors",
        isOver ? "border-sky-300 bg-sky-50" : "border-slate-300 bg-slate-100",
      ].join(" ")}
    >
      <header className="flex shrink-0 items-center justify-between gap-2 px-3 pt-3 pb-2">
        <h2 className="flex items-center gap-2 text-sm font-medium text-slate-700">
          <span
            aria-hidden
            className={`size-2.5 shrink-0 rounded-full ${phaseDot(status)}`}
          />
          {phaseLabel(status)}
        </h2>
        <span className="text-xs tabular-nums text-slate-400">{cards.length}</span>
      </header>

      <ul
        ref={setNodeRef}
        className="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto px-2 pb-2"
      >
        <SortableContext
          items={cards.map((card) => card.project.id)}
          strategy={verticalListSortingStrategy}
        >
          {cards.map((card) => (
            <SortableProjectCard
              key={card.project.id}
              card={card}
              maintenant={maintenant}
              onIntervenantsChange={onIntervenantsChange}
              onOpen={onOpen}
              frozen={frozen}
            />
          ))}
        </SortableContext>

        {/* A <ul> only takes <li>: a bare <p> would break hydration. */}
        {cards.length === 0 && (
          <li className="px-1 py-6 text-center text-xs text-slate-400">
            {frozen ? "Aucune mission ne répond aux filtres" : "Aucune mission"}
          </li>
        )}
      </ul>
    </section>
  );
}

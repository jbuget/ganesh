"use client";

import { ArrowDown, ArrowUp, ChevronsUpDown } from "lucide-react";

import { TableHead } from "@/components/ui/table";
import type { SortColumn, MissionSort } from "@/lib/mission-sort";

interface SortableColumnHeaderProps {
  column: SortColumn;
  label: string;
  sorted: MissionSort;
  onBasculer: (column: SortColumn) => void;
  /** Les colonnes de nombres s'alignent a droite, en-tete compris. */
  aDroite?: boolean;
}

/**
 * A column header the table gets arranged by.
 *
 * The double arrow only appears when hovering the header aimed at: nine
 * columns calling for attention at once would no longer say which one orders
 * the list. The one that does keeps its arrow showing.
 */
export function SortableColumnHeader({
  column,
  label,
  sorted,
  onBasculer,
  aDroite = false,
}: SortableColumnHeaderProps) {
  const is_active = sorted.column === column;
  const croissant = sorted.direction === "asc";

  return (
    <TableHead
      aria-sort={is_active ? (croissant ? "ascending" : "descending") : "none"}
      className={aDroite ? "text-right" : undefined}
    >
      <button
        type="button"
        onClick={() => onBasculer(column)}
        className={`group -mx-1 flex cursor-pointer items-center gap-1 rounded px-1 py-0.5 transition-colors hover:bg-slate-200 ${
          aDroite ? "ml-auto" : ""
        }`}
      >
        {label}
        {is_active ? (
          croissant ? (
            <ArrowUp className="size-3.5 shrink-0" aria-label="Ordre croissant" />
          ) : (
            <ArrowDown className="size-3.5 shrink-0" aria-label="Ordre décroissant" />
          )
        ) : (
          <ChevronsUpDown
            className="size-3.5 shrink-0 text-slate-400 opacity-0 transition-opacity group-hover:opacity-100"
            aria-hidden
          />
        )}
      </button>
    </TableHead>
  );
}

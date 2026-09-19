"use client";

import { ArrowDown, ArrowUp, ChevronsUpDown } from "lucide-react";

import { TableHead } from "@/components/ui/table";
import type { SortColumn, MissionSort } from "@/lib/mission-sort";

interface SortableColumnHeaderProps {
  column: SortColumn;
  label: string;
  sorted: MissionSort;
  onToggle: (column: SortColumn) => void;
  /** Number columns align right, heading included. */
  alignRight?: boolean;
  /** What the column imposes on its header: width, sticking to the left. */
  className?: string;
}

/**
 * A column header the table gets arranged by.
 *
 * The mark always shows, whether the column orders the list or not: a sort one
 * has to hover to discover is a sort nobody uses. The idle one is a faint
 * double chevron pointing both ways, the one in force a full arrow saying
 * which way — shape and tint tell them apart at a glance, without either
 * hiding.
 *
 * The whole cell answers the click, not the title alone: between two long
 * column names, the target was a few characters wide and nothing said where it
 * ended.
 */
export function SortableColumnHeader({
  column,
  label,
  sorted,
  onToggle,
  alignRight = false,
  className,
}: SortableColumnHeaderProps) {
  const is_active = sorted.column === column;
  const ascending = sorted.direction === "asc";

  return (
    // No padding of its own: the button takes the whole cell, and it is the
    // button that spaces the title off the edges.
    <TableHead
      aria-sort={is_active ? (ascending ? "ascending" : "descending") : "none"}
      className={["p-0", className ?? ""].join(" ").trim()}
    >
      <button
        type="button"
        onClick={() => onToggle(column)}
        className={`group flex h-10 w-full cursor-pointer items-center gap-1 px-2 transition-colors hover:bg-slate-200 ${
          alignRight ? "justify-end" : ""
        }`}
      >
        {label}
        {is_active ? (
          ascending ? (
            <ArrowUp className="size-3.5 shrink-0" aria-label="Ordre croissant" />
          ) : (
            <ArrowDown className="size-3.5 shrink-0" aria-label="Ordre décroissant" />
          )
        ) : (
          <ChevronsUpDown
            // Faint enough not to compete with the column in force, dark
            // enough to be seen without hovering.
            className="size-3.5 shrink-0 text-slate-400 transition-colors group-hover:text-slate-600"
            aria-hidden
          />
        )}
      </button>
    </TableHead>
  );
}

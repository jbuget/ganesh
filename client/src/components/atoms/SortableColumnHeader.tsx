"use client";

import { ArrowDown, ArrowUp, ChevronsUpDown } from "lucide-react";

import { TableHead } from "@/components/ui/table";
import type { ColumnSort } from "@/lib/table-sort";

interface SortableColumnHeaderProps<Column extends string> {
  column: Column;
  label: string;
  sorted: ColumnSort<Column>;
  onToggle: (column: Column) => void;
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
 *
 * Which columns there are is the table's business, not the header's: it is told
 * the column it carries and hands it back on a click, so the mission reference
 * list and the team list share the same header without sharing their columns.
 */
export function SortableColumnHeader<Column extends string>({
  column,
  label,
  sorted,
  onToggle,
  alignRight = false,
  className,
}: SortableColumnHeaderProps<Column>) {
  const isActive = sorted.column === column;
  const ascending = sorted.direction === "asc";

  return (
    // No padding of its own: the button takes the whole cell, and it is the
    // button that spaces the title off the edges.
    <TableHead
      aria-sort={isActive ? (ascending ? "ascending" : "descending") : "none"}
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
        {isActive ? (
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

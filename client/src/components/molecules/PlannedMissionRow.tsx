"use client";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical } from "lucide-react";

import { LandingDate } from "@/components/atoms/LandingDate";
import { MissionLoadCell } from "@/components/atoms/MissionLoadCell";
import { PlanBlockerNote } from "@/components/atoms/PlanBlockerNote";
import { PriorityMark } from "@/components/atoms/PriorityMark";
import { TableCell, TableRow } from "@/components/ui/table";
import type { PlannedMissionResponse } from "@/lib/api/generated/model";
import { phaseDot, phaseLabel } from "@/lib/board";
import { formatDecimalDays } from "@/lib/dates";

interface PlannedMissionRowProps {
  mission: PlannedMissionResponse;
  /** The week columns, in order: the row draws one cell per week. */
  weeks: string[];
  /** Its rank in the backlog, which is what a move changes. */
  rank: number;
}

/**
 * One mission of the plan: what it is, when it lands, and the weeks it takes.
 *
 * The handle on the left is the whole point of the screen: moving the row asks
 * the server what that order would cost, and the dates on every other row
 * answer. Nothing is written — the board only moves if someone decides to move
 * it there.
 */
export function PlannedMissionRow({ mission, weeks, rank }: PlannedMissionRowProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: mission.project_id });

  const byWeek = new Map(mission.weeks.map((week) => [week.week, week.days]));

  return (
    <TableRow
      ref={setNodeRef}
      style={{ transform: CSS.Translate.toString(transform), transition }}
      className={isDragging ? "bg-sky-50" : undefined}
    >
      <TableCell className="sticky left-0 z-10 bg-white">
        <div className="flex items-center gap-2">
          <button
            type="button"
            aria-label={`Déplacer ${mission.label}`}
            className="cursor-grab touch-none rounded p-0.5 text-slate-300 transition-colors hover:text-slate-500 active:cursor-grabbing"
            {...attributes}
            {...listeners}
          >
            <GripVertical className="size-4" />
          </button>

          <span className="w-5 shrink-0 text-xs text-slate-400 tabular-nums">
            {rank + 1}
          </span>

          {mission.status && (
            <span
              aria-hidden
              title={phaseLabel(mission.status)}
              className={`size-2 shrink-0 rounded-full ${phaseDot(mission.status)}`}
            />
          )}

          <span className="truncate text-sm text-slate-800" title={mission.label}>
            {/* A work package is indented under nothing here: the plan serves a
                flat queue, and its parent is a column of its own on the list. */}
            {mission.label}
          </span>

          <PriorityMark value={mission.priority} />
        </div>
      </TableCell>

      <TableCell className="text-right text-sm text-slate-600 tabular-nums">
        {mission.remaining_days > 0 ? formatDecimalDays(mission.remaining_days) : "—"}
      </TableCell>

      <TableCell className="whitespace-nowrap">
        {mission.blocker ? (
          <PlanBlockerNote reason={mission.blocker} />
        ) : (
          <LandingDate endsOn={mission.ends_on} slippageDays={mission.slippage_days} />
        )}
      </TableCell>

      {weeks.map((week) => (
        <TableCell key={week} className="px-1">
          <MissionLoadCell days={byWeek.get(week) ?? 0} />
        </TableCell>
      ))}
    </TableRow>
  );
}

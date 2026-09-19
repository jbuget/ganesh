"use client";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical } from "lucide-react";

import { LandingDate } from "@/components/atoms/LandingDate";
import { MissionLoadCell } from "@/components/atoms/MissionLoadCell";
import { PlanAssigneesPicker } from "@/components/atoms/PlanAssigneesPicker";
import { PlanBlockerNote } from "@/components/atoms/PlanBlockerNote";
import { PriorityMark } from "@/components/atoms/PriorityMark";
import { RankControls } from "@/components/atoms/RankControls";
import { TableCell, TableRow } from "@/components/ui/table";
import type {
  PlanMemberResponse,
  PlannedMissionResponse,
} from "@/lib/api/generated/model";
import { phaseDot, phaseLabel } from "@/lib/board";
import { formatDecimalDays } from "@/lib/dates";

interface PlannedMissionRowProps {
  mission: PlannedMissionResponse;
  /** The week columns, in order: the row draws one cell per week. */
  weeks: string[];
  /** Its rank in the backlog, which is what a move changes. */
  rank: number;
  isLast: boolean;
  /** Everyone the work could be placed on. */
  team: PlanMemberResponse[];
  onTop: (projectId: number) => void;
  onUp: (projectId: number) => void;
  onDown: (projectId: number) => void;
  onStaff: (projectId: number, userIds: number[]) => void;
}

/**
 * One mission of the plan: what it is, who carries it, when it lands.
 *
 * The two levers sit on the row itself, and show at all times. Reorder it, or
 * put somebody else on it, and the server says what that would cost — the
 * dates on every other row answer. Nothing is written: the board only moves if
 * someone decides to move it there.
 */
export function PlannedMissionRow({
  mission,
  weeks,
  rank,
  isLast,
  team,
  onTop,
  onUp,
  onDown,
  onStaff,
}: PlannedMissionRowProps) {
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
        <div className="flex items-center gap-1">
          <button
            type="button"
            aria-label={`Déplacer ${mission.label}`}
            className="cursor-grab touch-none rounded p-0.5 text-slate-300 transition-colors hover:text-slate-500 active:cursor-grabbing"
            {...attributes}
            {...listeners}
          >
            <GripVertical className="size-4" />
          </button>

          <span className="w-5 shrink-0 text-right text-xs text-slate-400 tabular-nums">
            {rank + 1}
          </span>

          <RankControls
            label={mission.label}
            isFirst={rank === 0}
            isLast={isLast}
            onTop={() => onTop(mission.project_id)}
            onUp={() => onUp(mission.project_id)}
            onDown={() => onDown(mission.project_id)}
          />
        </div>
      </TableCell>

      {/* The width is set on the content and not on the header alone: the
          table sizes itself on what it holds, and a mission named in a full
          sentence would otherwise push the weeks out of sight. */}
      <TableCell className="sticky left-[7.5rem] z-10 bg-white">
        <div className="flex w-[22rem] items-center gap-2">
          {mission.status && (
            <span
              aria-hidden
              title={phaseLabel(mission.status)}
              className={`size-2 shrink-0 rounded-full ${phaseDot(mission.status)}`}
            />
          )}

          {/* `min-w-0` is what lets the truncation happen: a flex child
              refuses to shrink below its content without it. */}
          <span
            className="min-w-0 flex-1 truncate text-sm text-slate-800"
            title={mission.label}
          >
            {mission.label}
          </span>

          <span className="shrink-0">
            <PriorityMark value={mission.priority} />
          </span>
        </div>
      </TableCell>

      <TableCell>
        <PlanAssigneesPicker
          label={mission.label}
          team={team}
          assignees={mission.assignees}
          onChange={(userIds) => onStaff(mission.project_id, userIds)}
        />
      </TableCell>

      <TableCell className="text-right text-sm text-slate-600 tabular-nums">
        {mission.remaining_days > 0 ? formatDecimalDays(mission.remaining_days) : "—"}
      </TableCell>

      <TableCell className="whitespace-nowrap">
        {mission.blocker ? (
          <PlanBlockerNote reason={mission.blocker} />
        ) : (
          <LandingDate
            endsOn={mission.ends_on}
            slippageDays={mission.slippage_days}
            isLate={mission.is_late}
          />
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

"use client";

import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";

import { WeekColumnHeader } from "@/components/atoms/WeekColumnHeader";
import { PlannedMissionRow } from "@/components/molecules/PlannedMissionRow";
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type {
  PlanMemberResponse,
  PlannedMissionResponse,
} from "@/lib/api/generated/model";
import { formatMonthOf } from "@/lib/dates";

interface WorkloadTimelineProps {
  missions: PlannedMissionResponse[];
  weeks: string[];
  /** Everyone the work could be placed on. */
  team: PlanMemberResponse[];
  /** Puts a mission at a new rank, which re-asks the whole projection. */
  onMove: (projectId: number, to: number) => void;
  onTop: (projectId: number) => void;
  onUp: (projectId: number) => void;
  onDown: (projectId: number) => void;
  /** Supposes a mission is carried by these people, and nobody else. */
  onStaff: (projectId: number, userIds: number[]) => void;
}

/** Whether a week opens a month, which is where the month label goes. */
function opensMonth(weeks: string[], index: number): boolean {
  if (index === 0) return true;
  return weeks[index].slice(0, 7) !== weeks[index - 1].slice(0, 7);
}

/**
 * The backlog in the order it is served, and the weeks each mission takes.
 *
 * Read down the first columns, it says when things land and what is late. Read
 * across, the blocks draw the span each mission occupies — a gantt nobody drew
 * by hand, since it comes out of the room the diaries actually leave.
 *
 * It renders what it is given and asks for the rest: the order, the horizon and
 * the fetching belong to the screen around it.
 */
export function WorkloadTimeline({
  missions,
  weeks,
  team,
  onMove,
  onTop,
  onUp,
  onDown,
  onStaff,
}: WorkloadTimelineProps) {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  function handleDragEnd({ active, over }: DragEndEvent) {
    if (!over || active.id === over.id) return;
    const to = missions.findIndex((mission) => mission.project_id === over.id);
    if (to !== -1) onMove(Number(active.id), to);
  }

  if (missions.length === 0) {
    return (
      <p className="py-12 text-center text-sm text-slate-400">
        Aucune mission à planifier : tout ce qui n&apos;est pas en exploitation est
        terminé ou archivé.
      </p>
    );
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragEnd={handleDragEnd}
    >
      <div className="w-max pr-6 [&_[data-slot=table-container]]:overflow-visible">
        <Table>
          <TableHeader className="sticky top-0 z-20 [&_th]:border-b [&_th]:border-b-slate-500 [&_th]:bg-slate-50">
            <TableRow>
              <TableHead className="sticky left-0 z-30 w-[7.5rem] bg-slate-50">
                Rang
              </TableHead>
              <TableHead className="sticky left-[7.5rem] z-30 bg-slate-50">
                Mission
              </TableHead>
              <TableHead className="w-40">Intervenants</TableHead>
              <TableHead className="w-24 text-right">Reste (j)</TableHead>
              <TableHead className="w-64">Atterrissage</TableHead>
              {weeks.map((week, index) => (
                <TableHead key={week} className="w-14 px-1">
                  <WeekColumnHeader
                    week={week}
                    opensMonth={opensMonth(weeks, index)}
                    monthLabel={formatMonthOf(week)}
                  />
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>

          <TableBody>
            <SortableContext
              items={missions.map((mission) => mission.project_id)}
              strategy={verticalListSortingStrategy}
            >
              {missions.map((mission, rank) => (
                <PlannedMissionRow
                  key={mission.project_id}
                  mission={mission}
                  weeks={weeks}
                  rank={rank}
                  isLast={rank === missions.length - 1}
                  team={team}
                  onTop={onTop}
                  onUp={onUp}
                  onDown={onDown}
                  onStaff={onStaff}
                />
              ))}
            </SortableContext>
          </TableBody>
        </Table>
      </div>
    </DndContext>
  );
}

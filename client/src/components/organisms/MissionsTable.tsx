"use client";

import { Fragment } from "react";

import { SortableColumnHeader } from "@/components/atoms/SortableColumnHeader";
import { MissionRow } from "@/components/molecules/MissionRow";
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  CATEGORY_COLUMN,
  DAYS_COLUMN,
  LEFT_MARGIN,
  MEMBERS_COLUMN,
  MISSIONS_TABLE,
  NAME_COLUMN,
  PHASE_COLUMN,
  PRIORITY_COLUMN,
  STRONG_SEPARATOR,
  THREAD_COLUMN,
} from "@/lib/mission-columns";
import type { MissionSort, SortColumn } from "@/lib/mission-sort";
import type { ProjectNode } from "@/lib/project-tree";

interface MissionsTableProps {
  /** The missions to draw, already filtered and already in order. */
  tree: ProjectNode[];
  sorted: MissionSort;
  onSort: (column: SortColumn) => void;
  /** Whether a project's work packages are showing. */
  isExpanded: (projectId: number) => boolean;
  onToggle: (projectId: number) => void;
  /** One reference time for every row, so « il y a 3 h » does not drift. */
  now: Date;
  onOpen: (projectId: number) => void;
  /** Opens a mission on its thread, where the preview stops. */
  onOpenThread: (projectId: number) => void;
}

/**
 * The reference list as a table: ten columns, a project and its work packages
 * per block.
 *
 * It draws what it is given and asks for the rest: no criteria of its own, no
 * fetching, no opinion on what to show when there is nothing — the screen
 * around it answers that, in its own words. That is what lets the same table
 * serve another page.
 */
export function MissionsTable({
  tree,
  sorted,
  onSort,
  isExpanded,
  onToggle,
  now,
  onOpen,
  onOpenThread,
}: MissionsTableProps) {
  return (
    // The shadcn container opens a scrolling context that would hold the
    // header inside the table: we neutralise it so the `sticky` latches onto
    // the page's scrolling area.
    // The box sizes itself on the table rather than on the available room: the
    // padding of the scrolling area does not count towards what it can travel,
    // and without that band on the right the last column would butt against
    // the window edge.
    <div className="w-max pr-6 [&_[data-slot=table-container]]:overflow-visible">
      <Table className={MISSIONS_TABLE}>
        {/* Sixty rows pass under the header: without it, one no longer knows
            which column one is reading by the time one reaches the bottom. The
            background sits on the cells and not on the row: in a table, a row's
            background paints under the lines that scroll. */}
        <TableHeader className="sticky top-0 z-10 [&_th]:border-b [&_th]:border-b-slate-500 [&_th]:bg-slate-50">
          <TableRow>
            <SortableColumnHeader
              column="project"
              label="Projet"
              sorted={sorted}
              onToggle={onSort}
              className={`${NAME_COLUMN} ${LEFT_MARGIN}`}
            />
            {/* The follow-up thread: its icon carries the meaning, not a title. */}
            {/* Only the right-hand line reaches into the header: it marks where
                the pinned part stops, over the full height of the table. The
                left-hand one separates two columns, and so starts below their
                titles. */}
            <TableHead className={`${THREAD_COLUMN} ${STRONG_SEPARATOR}`} />
            <SortableColumnHeader
              column="phase"
              label="Phase"
              sorted={sorted}
              onToggle={onSort}
              className={PHASE_COLUMN}
            />
            <SortableColumnHeader
              column="priority"
              label="Priorité"
              sorted={sorted}
              onToggle={onSort}
              className={PRIORITY_COLUMN}
            />
            <SortableColumnHeader
              column="category"
              label="Catégorie"
              sorted={sorted}
              onToggle={onSort}
              className={CATEGORY_COLUMN}
            />
            {/* Build against its estimate, run apart: the two answer different
                questions, and a single column carrying both would no longer
                sort. */}
            <SortableColumnHeader
              column="build"
              label="Build"
              sorted={sorted}
              onToggle={onSort}
              alignRight
              className={DAYS_COLUMN}
            />
            <SortableColumnHeader
              column="run"
              label="Run"
              sorted={sorted}
              onToggle={onSort}
              alignRight
              className={DAYS_COLUMN}
            />
            {/* Who looks after it does not sort: a column of badges has no order
                the reader would have in mind. */}
            <TableHead className={MEMBERS_COLUMN}>Référents</TableHead>
            <TableHead className={MEMBERS_COLUMN}>Intervenants</TableHead>
            {/* Last, and without a width: it takes what is left when the screen
                is wider than the table. */}
            <TableHead>Liens</TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          {tree.map(({ mission, workPackages }) => {
            const expanded = isExpanded(mission.project.id);

            return (
              <Fragment key={mission.project.id}>
                <MissionRow
                  mission={mission}
                  isWorkPackage={mission.project.kind === "work_package"}
                  workPackages={workPackages.length}
                  expanded={expanded}
                  onToggle={() => onToggle(mission.project.id)}
                  now={now}
                  onOpen={() => onOpen(mission.project.id)}
                  onOpenThread={() => onOpenThread(mission.project.id)}
                />
                {expanded &&
                  workPackages.map((workPackage) => (
                    <MissionRow
                      key={workPackage.project.id}
                      mission={workPackage}
                      isWorkPackage
                      now={now}
                      onOpen={() => onOpen(workPackage.project.id)}
                      onOpenThread={() => onOpenThread(workPackage.project.id)}
                    />
                  ))}
              </Fragment>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}

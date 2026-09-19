"use client";

import { DndContext, DragOverlay } from "@dnd-kit/core";
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
  DEPARTMENTS_COLUMN,
  GO_LIVE_COLUMN,
  LEFT_MARGIN,
  MEMBERS_COLUMN,
  MISSIONS_TABLE,
  NAME_COLUMN,
  NO_HIDDEN_COLUMN,
  PHASE_COLUMN,
  PRIORITY_COLUMN,
  STRONG_SEPARATOR,
  THREAD_COLUMN,
  tableWidth,
  type ColumnKey,
  type HiddenColumns,
} from "@/lib/mission-columns";
import type { MissionSort, SortColumn } from "@/lib/mission-sort";
import { TABLE_HEADER } from "@/lib/table-frame";
import { useMissionDrag } from "@/lib/use-mission-drag";
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
  /** The columns put away. Nothing put away shows the whole panorama. */
  hidden?: HiddenColumns;
  /**
   * Makes a mission a work package of the project it is dropped onto.
   *
   * Given, the rows carry a handle; left out, the table draws itself as it
   * always has. The gesture is the pointer's alone — the keyboard reaches the
   * same move through the mission panel's menu.
   */
  onAttach?: (missionId: number, parentId: number) => void | Promise<void>;
}

/**
 * The reference list as a table: twelve columns, a project and its work
 * packages per block.
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
  hidden = NO_HIDDEN_COLUMN,
  onAttach,
}: MissionsTableProps) {
  const shows = (column: ColumnKey) => !hidden.has(column);
  // The gesture lives in a hook, as the board's does: the table draws what it
  // is given, and a drag is not a drawing.
  const drag = useMissionDrag(tree, onAttach);

  return (
    <DndContext
      sensors={drag.sensors}
      collisionDetection={drag.collisionDetection}
      onDragStart={drag.onDragStart}
      onDragEnd={drag.onDragEnd}
      onDragCancel={drag.onDragCancel}
    >
      {/* The shadcn container opens a scrolling context that would hold the
          header inside the table: we neutralise it so the `sticky` latches
          onto the page's scrolling area.
          The box sizes itself on the table rather than on the available room:
          the padding of the scrolling area does not count towards what it can
          travel, and without that band on the right the last column would butt
          against the window edge. */}
      <div
        onClickCapture={drag.onClickCapture}
        onPointerDownCapture={drag.onPointerDownCapture}
        className={[
          "w-max pr-6 [&_[data-slot=table-container]]:overflow-visible",
          // Nothing is selected while something is being carried: a slide
          // across a table otherwise paints three rows blue behind the copy.
          drag.dragged ? "select-none" : "",
        ].join(" ")}
      >
        {/* The width is carried in figures rather than by a class: Tailwind
          cannot write one for a span only known once the address has said
          which columns are put away. */}
        <Table className={MISSIONS_TABLE} style={{ width: tableWidth(hidden) }}>
          {/* Sixty rows pass under the header: the band of titles is the
            application's own, and stays in sight. */}
          <TableHeader className={TABLE_HEADER}>
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
              {shows("phase") && (
                <SortableColumnHeader
                  column="phase"
                  label="Phase"
                  sorted={sorted}
                  onToggle={onSort}
                  className={PHASE_COLUMN}
                />
              )}
              {shows("priority") && (
                <SortableColumnHeader
                  column="priority"
                  label="Priorité"
                  sorted={sorted}
                  onToggle={onSort}
                  className={PRIORITY_COLUMN}
                />
              )}
              {shows("category") && (
                <SortableColumnHeader
                  column="category"
                  label="Catégorie"
                  sorted={sorted}
                  onToggle={onSort}
                  className={CATEGORY_COLUMN}
                />
              )}
              {/* Who the mission serves does not sort: a column of chips has no
                order the reader would have in mind. It follows the axis,
                which answers the neighbouring question — what the mission is
                for, then whom it is for. */}
              {shows("departments") && (
                <TableHead className={DEPARTMENTS_COLUMN}>Départements</TableHead>
              )}
              {/* Build against its estimate, run apart: the two answer different
                questions, and a single column carrying both would no longer
                sort. */}
              {shows("build") && (
                <SortableColumnHeader
                  column="build"
                  label="Build"
                  sorted={sorted}
                  onToggle={onSort}
                  alignRight
                  className={DAYS_COLUMN}
                />
              )}
              {shows("run") && (
                <SortableColumnHeader
                  column="run"
                  label="Run"
                  sorted={sorted}
                  onToggle={onSort}
                  alignRight
                  className={DAYS_COLUMN}
                />
              )}
              {/* What it weighs, then when it lands: the date the team announced,
                the one the roadmap posts. It sorts, and that is what the
                column is for — reading what comes next in order. */}
              {shows("goLive") && (
                <SortableColumnHeader
                  column="goLive"
                  label="Mise en service"
                  sorted={sorted}
                  onToggle={onSort}
                  className={GO_LIVE_COLUMN}
                />
              )}
              {/* Who looks after it does not sort: a column of badges has no order
                the reader would have in mind. */}
              {shows("leads") && (
                <TableHead className={MEMBERS_COLUMN}>Référents</TableHead>
              )}
              {shows("contributors") && (
                <TableHead className={MEMBERS_COLUMN}>Intervenants</TableHead>
              )}
              {/* Last, and without a width: it takes what is left when the screen
                is wider than the table. The catalogue is the end of the
                reading — what the mission became public as, once everything
                that steers it has been read. */}
              {shows("published") && <TableHead>Publié</TableHead>}
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
                    {...drag.gesture(mission, workPackages.length)}
                    expanded={expanded}
                    onToggle={() => onToggle(mission.project.id)}
                    now={now}
                    onOpen={() => onOpen(mission.project.id)}
                    onOpenThread={() => onOpenThread(mission.project.id)}
                    hidden={hidden}
                  />
                  {expanded &&
                    workPackages.map((workPackage) => (
                      <MissionRow
                        key={workPackage.project.id}
                        mission={workPackage}
                        isWorkPackage
                        {...drag.gesture(workPackage, 0)}
                        now={now}
                        onOpen={() => onOpen(workPackage.project.id)}
                        onOpenThread={() => onOpenThread(workPackage.project.id)}
                        hidden={hidden}
                      />
                    ))}
                </Fragment>
              );
            })}
          </TableBody>
        </Table>

        {/* What is being carried follows the cursor, freed from the table: a row
          of ten columns dragged whole would hide the projects it is aimed at. */}
        <DragOverlay dropAnimation={null}>
          {drag.dragged && (
            <span className="inline-block w-max max-w-md truncate rounded border border-slate-300 bg-white px-2 py-1 text-sm whitespace-nowrap text-slate-800 shadow-lg">
              {drag.dragged.project.label}
            </span>
          )}
        </DragOverlay>
      </div>
    </DndContext>
  );
}

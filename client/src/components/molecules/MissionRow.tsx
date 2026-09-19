"use client";

import { useDraggable, useDroppable } from "@dnd-kit/core";
import { ChevronRight, GripVertical } from "lucide-react";

import { BuildCost } from "@/components/atoms/BuildCost";
import { CategoryMark } from "@/components/atoms/CategoryMark";
import { MarkdownView } from "@/components/atoms/MarkdownView";
import { MemberAvatars } from "@/components/atoms/MemberAvatars";
import { PriorityMark } from "@/components/atoms/PriorityMark";
import { ProjectLinks } from "@/components/atoms/ProjectLinks";
import { RunCost } from "@/components/atoms/RunCost";
import { UpdatesCounter } from "@/components/atoms/UpdatesCounter";
import { TableCell, TableRow } from "@/components/ui/table";
import type { ProjectListItemResponse } from "@/lib/api/generated/model";
import { phaseLabel, phaseDot } from "@/lib/board";
import {
  LEFT_MARGIN,
  NAME_COLUMN,
  NO_HIDDEN_COLUMN,
  SEPARATOR,
  STRONG_SEPARATOR,
  THREAD_COLUMN,
  type ColumnKey,
  type HiddenColumns,
} from "@/lib/mission-columns";
import { since } from "@/lib/relative-dates";

interface MissionRowProps {
  mission: ProjectListItemResponse;
  /** A work package indents under its project, so the hierarchy reads. */
  isWorkPackage?: boolean;
  /** How many sub-projects the mission carries: none, nothing to fold. */
  workPackages?: number;
  /** Whether its sub-projects are visible. Collapsed by default. */
  expanded?: boolean;
  /** Shows or hides the sub-projects. */
  onToggle?: () => void;
  /** Freezes the reference time: without it, server and client would diverge. */
  now: Date;
  onOpen: () => void;
  /** Opens the mission on its thread, where the preview stops. */
  onOpenThread: () => void;
  /** The columns put away. Nothing put away shows the whole panorama. */
  hidden?: HiddenColumns;
  /**
   * Whether the row may be picked up and dropped onto a project.
   *
   * Left out where the table offers no such gesture: the handle's gutter is
   * only reserved when there is something to grab in the list, so the names
   * fall on the same vertical from one row to the next either way.
   */
  movable?: boolean;
  /** Whether dropping what is being dragged here would attach it. */
  receiving?: boolean;
}

/**
 * A mission from the reference list, column by column.
 *
 * The row still carries no action: it shows what it takes to compare two
 * missions at a glance — where they stand, what they weigh, who looks after
 * them — and everything that changes goes on happening in the panel, from a
 * single place.
 */
export function MissionRow({
  mission,
  isWorkPackage = false,
  workPackages = 0,
  expanded = false,
  onToggle,
  now,
  onOpen,
  onOpenThread,
  hidden = NO_HIDDEN_COLUMN,
  movable,
  receiving = false,
}: MissionRowProps) {
  const shows = (column: ColumnKey) => !hidden.has(column);
  const { project } = mission;
  const latest = mission.latest_update;

  // Both hooks are called on every row and turned off where the gesture means
  // nothing: what a row may do changes with the drag, and hooks may not.
  //
  // What is dragged is the row, what one takes hold of is the handle: the two
  // are declared apart on purpose. Hanging the gesture on the handle alone
  // would make the copy under the cursor the size of a grip, sixteen pixels
  // wide, and a label would come out stacked one word per line inside it.
  const {
    attributes,
    listeners,
    setNodeRef: setDraggedRef,
    setActivatorNodeRef: setHandleRef,
    isDragging,
  } = useDraggable({ id: project.id, disabled: movable !== true });
  const { setNodeRef: setTargetRef, isOver } = useDroppable({
    id: project.id,
    disabled: !receiving,
  });
  const isTarget = receiving && isOver;

  /** The row is both what moves and what receives: one node, two roles. */
  function setRowRef(row: HTMLTableRowElement | null) {
    setDraggedRef(row);
    setTargetRef(row);
  }

  // Folded, a row tells what the whole service cost — its own build, that of
  // its evolutions, and the run of all of it. Unfolded, every row speaks of
  // itself again, and the totals would be counted twice.
  //
  // The reading follows what the screen shows, not what a filter kept: a
  // mission whose work packages are hidden still carries their cost, because
  // it is still the cost of that service. For a mission without any, both
  // figures are the same anyway.
  const cost = expanded ? mission.cost : mission.tree_cost;

  // The latest message in full and formatted, as it reads in the thread: a
  // truncated preview would force opening the panel for the end of a sentence.
  const preview = latest && (
    <>
      {/* The rule separates the signature from the words: without it, the first
          line of the message reads as the continuation of the header. Negative
          margins carry it to the edges of the bubble, whose padding it
          crosses. */}
      <p className="-mx-3 mb-2 border-b border-slate-200 px-3 pb-2 text-xs text-slate-500">
        <span className="font-medium text-slate-700">{latest.author.display_name}</span>{" "}
        · {since(latest.published_at, now)}
      </p>
      <MarkdownView body={latest.body} />
    </>
  );

  return (
    // The row takes the page background, the pinned cells white: what stays in
    // sight is thereby lifted off what scrolls underneath, and the name reads
    // as the anchor of the line rather than as its first column. Those cells
    // follow the row one step behind — page background where it goes a shade
    // darker — so hovering marks the whole line without flattening the relief.
    // Every tint is solid: a transparent one would let what slides underneath
    // read through the pinned columns.
    <TableRow
      ref={setRowRef}
      onClick={onOpen}
      className={[
        "group cursor-pointer bg-slate-50 hover:bg-slate-100 has-aria-expanded:bg-slate-100",
        // The row taken hold of fades: what one is carrying reads in the
        // overlay under the cursor, not twice.
        isDragging ? "opacity-40" : "",
        // The project about to take it in is underlined and overlined rather
        // than tinted: a tint would have to beat the pinned cells' own, which
        // are opaque.
        //
        // Every cell draws its own two rules, rather than the row drawing one
        // around itself: the pinned cells paint in front of the row, and an
        // outline carried by the row stopped where the name begins — exactly
        // where the eye is. Inset shadows rather than borders, because a
        // border would add its thickness to the row and make the table jump
        // as the cursor passes.
        isTarget
          ? "[&>td]:shadow-[inset_0_2px_0_0_var(--color-sky-500),inset_0_-2px_0_0_var(--color-sky-500)]"
          : "",
      ].join(" ")}
    >
      {/* No `z`: a pinned cell already passes in front of ordinary cells, and
          claiming one would send it in front of the header, which must stay
          above everything that scrolls. */}
      <TableCell
        className={[
          NAME_COLUMN,
          LEFT_MARGIN,
          SEPARATOR,
          "bg-white group-hover:bg-slate-50 group-has-[[aria-expanded=true]]:bg-slate-50",
          isWorkPackage ? "pl-14" : "",
        ].join(" ")}
      >
        <span className="flex items-center gap-2">
          {/* The handle shows on hover and keeps its place the rest of the
              time: appearing out of nowhere would shift every name to the
              right as the cursor passes. */}
          {movable !== undefined && (
            <span className="-ml-1 w-4 shrink-0">
              {movable && (
                <button
                  type="button"
                  ref={setHandleRef}
                  aria-label={`Déplacer ${project.label}`}
                  title="Faire glisser sur un projet pour l'y rattacher"
                  // The whole row opens the mission: without stopping
                  // propagation, taking hold of the handle would open the panel.
                  onClick={(event) => event.stopPropagation()}
                  // Pressing on the handle must take hold of the row, not start
                  // selecting the text of the table: the browser reads a press
                  // and a slide as a selection, and would paint three rows blue
                  // under the copy being dragged. Refusing the default of the
                  // mouse event leaves the pointer events dnd-kit listens to
                  // untouched.
                  onMouseDown={(event) => event.preventDefault()}
                  className="cursor-grab text-slate-300 opacity-0 transition-opacity group-hover:opacity-100 focus-visible:opacity-100 active:cursor-grabbing"
                  {...listeners}
                  {...attributes}
                >
                  <GripVertical className="size-4" aria-hidden />
                </button>
              )}
            </span>
          )}

          {/* The bracket ties the work package to its project: without it,
              indentation alone gets lost as soon as a long line wraps. */}
          {isWorkPackage && (
            <span aria-hidden className="-ml-4 text-slate-300">
              └
            </span>
          )}

          {/* A sixty-row reference list reads poorly fully expanded: the
              chevron gives a project's detail on demand. The gutter stays even
              without sub-projects, otherwise the names would no longer fall on
              the same vertical from one row to the next. */}
          {!isWorkPackage &&
            (workPackages > 0 ? (
              <button
                type="button"
                aria-expanded={expanded}
                aria-label={`${expanded ? "Masquer" : "Afficher"} ${
                  workPackages > 1
                    ? `les ${workPackages} sous-projets`
                    : "le sous-projet"
                } de ${project.label}`}
                // The whole row opens the mission: without stopping
                // propagation, folding would open the panel at the same time.
                onClick={(event) => {
                  event.stopPropagation();
                  onToggle?.();
                }}
                className="cursor-pointer rounded p-0.5 text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-700"
              >
                <ChevronRight
                  aria-hidden
                  className={`size-4 transition-transform ${expanded ? "rotate-90" : ""}`}
                />
              </button>
            ) : (
              <span aria-hidden className="size-5 shrink-0" />
            ))}
          <button
            type="button"
            // Truncated, the name stays readable in full on hover: the column
            // has a fixed width, and the reference list's labels overflow it.
            title={project.label}
            // The whole row responds to the mouse; this button gives the same
            // opening to the keyboard, without opening twice.
            onClick={(event) => {
              event.stopPropagation();
              onOpen();
            }}
            className={[
              "min-w-0 cursor-pointer truncate text-left",
              isWorkPackage ? "text-slate-600" : "font-medium text-slate-800",
            ].join(" ")}
          >
            {project.label}
          </button>
        </span>
      </TableCell>

      {/* The thread reads against the mission name, whose activity it
          reports: further away, one would no longer know which row it speaks
          of. The icon already says what the number counts, hence the empty
          heading. */}
      <TableCell
        className={[
          THREAD_COLUMN,
          STRONG_SEPARATOR,
          "bg-white group-hover:bg-slate-50 group-has-[[aria-expanded=true]]:bg-slate-50",
          "text-right",
        ].join(" ")}
      >
        <UpdatesCounter
          count={mission.comments}
          preview={preview}
          onOpen={onOpenThread}
        />
      </TableCell>

      {shows("phase") && (
        <TableCell>
          {project.status && (
            <span className="flex items-center gap-1.5 text-slate-700">
              <span
                aria-hidden
                className={`size-2.5 shrink-0 rounded-full ${phaseDot(project.status)}`}
              />
              {phaseLabel(project.status)}
            </span>
          )}
        </TableCell>
      )}

      {/* Priority follows phase, as in the sheet: where the mission stands,
          then what it must come before. */}
      {shows("priority") && (
        <TableCell>
          <PriorityMark value={project.priority} />
        </TableCell>
      )}

      {shows("category") && (
        <TableCell>
          <CategoryMark value={project.category} />
        </TableCell>
      )}

      {/* Build against its estimate, run apart: the estimate covered the
          construction alone, and comparing the whole life of a service to it
          would declare every living mission late. A zero is not a value to
          read: a mission nobody has declared on stays empty. */}
      {shows("build") && (
        <TableCell className="text-right tabular-nums text-slate-600">
          <BuildCost cost={cost} />
        </TableCell>
      )}

      {shows("run") && (
        <TableCell className="text-right tabular-nums text-slate-600">
          <RunCost cost={cost} />
        </TableCell>
      )}

      {shows("leads") && (
        <TableCell>
          <MemberAvatars members={mission.leads} />
        </TableCell>
      )}

      {shows("contributors") && (
        <TableCell>
          <MemberAvatars members={mission.contributors} />
        </TableCell>
      )}

      {/* Where the mission's work is written down. The icons stand on their
          own: in a row there is no room for their labels, which come back on
          hover. */}
      {shows("links") && (
        <TableCell>
          <ProjectLinks links={mission.links} />
        </TableCell>
      )}
    </TableRow>
  );
}

"use client";

import { ChevronRight } from "lucide-react";

import { CategoryMark } from "@/components/atoms/CategoryMark";
import { MarkdownView } from "@/components/atoms/MarkdownView";
import { MemberAvatars } from "@/components/atoms/MemberAvatars";
import { PriorityMark } from "@/components/atoms/PriorityMark";
import { UpdatesCounter } from "@/components/atoms/UpdatesCounter";
import { TableCell, TableRow } from "@/components/ui/table";
import type { ProjectListItemResponse } from "@/lib/api/generated/model";
import { phaseLabel, phaseDot } from "@/lib/board";
import { depuis } from "@/lib/relative-dates";

interface MissionRowProps {
  mission: ProjectListItemResponse;
  /** A work package indents under its project, so the hierarchy reads. */
  estLot?: boolean;
  /** How many sub-projects the mission carries: none, nothing to fold. */
  lots?: number;
  /** Whether its sub-projects are visible. Collapsed by default. */
  deplie?: boolean;
  /** Shows or hides the sub-projects. */
  onBasculer?: () => void;
  /** Freezes the reference time: without it, server and client would diverge. */
  maintenant: Date;
  onOpen: () => void;
  /** Opens the mission on its thread, where the preview stops. */
  onOpenFil: () => void;
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
  estLot = false,
  lots = 0,
  deplie = false,
  onBasculer,
  maintenant,
  onOpen,
  onOpenFil,
}: MissionRowProps) {
  const { project } = mission;
  const latest = mission.latest_update;

  // The latest message in full and formatted, as it reads in the thread: a
  // truncated preview would force opening the panel for the end of a sentence.
  const apercu = latest && (
    <>
      {/* The rule separates the signature from the words: without it, the first
          line of the message reads as the continuation of the header. Negative
          margins carry it to the edges of the bubble, whose padding it
          crosses. */}
      <p className="-mx-3 mb-2 border-b border-slate-200 px-3 pb-2 text-xs text-slate-500">
        <span className="font-medium text-slate-700">{latest.author.display_name}</span>{" "}
        · {depuis(latest.published_at, maintenant)}
      </p>
      <MarkdownView body={latest.body} />
    </>
  );

  return (
    <TableRow onClick={onOpen} className="cursor-pointer">
      <TableCell className={estLot ? "pl-14" : ""}>
        <span className="flex items-center gap-2">
          {/* The bracket ties the work package to its project: without it,
              indentation alone gets lost as soon as a long line wraps. */}
          {estLot && (
            <span aria-hidden className="-ml-4 text-slate-300">
              └
            </span>
          )}

          {/* A sixty-row reference list reads poorly fully expanded: the
              chevron gives a project's detail on demand. The gutter stays even
              without sub-projects, otherwise the names would no longer fall on
              the same vertical from one row to the next. */}
          {!estLot &&
            (lots > 0 ? (
              <button
                type="button"
                aria-expanded={deplie}
                aria-label={`${deplie ? "Masquer" : "Afficher"} ${
                  lots > 1 ? `les ${lots} sous-projets` : "le sous-projet"
                } de ${project.label}`}
                // The whole row opens the mission: without stopping
                // propagation, folding would open the panel at the same time.
                onClick={(event) => {
                  event.stopPropagation();
                  onBasculer?.();
                }}
                className="cursor-pointer rounded p-0.5 text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-700"
              >
                <ChevronRight
                  aria-hidden
                  className={`size-4 transition-transform ${deplie ? "rotate-90" : ""}`}
                />
              </button>
            ) : (
              <span aria-hidden className="size-5 shrink-0" />
            ))}
          <button
            type="button"
            // The whole row responds to the mouse; this button gives the same
            // opening to the keyboard, without opening twice.
            onClick={(event) => {
              event.stopPropagation();
              onOpen();
            }}
            className={[
              "cursor-pointer text-left",
              estLot ? "text-slate-600" : "font-medium text-slate-800",
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
      <TableCell className="w-12 text-right">
        <UpdatesCounter count={mission.comments} apercu={apercu} onOpen={onOpenFil} />
      </TableCell>

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

      {/* Priority follows phase, as in the sheet: where the mission stands,
          then what it must come before. */}
      <TableCell>
        <PriorityMark value={project.priority} />
      </TableCell>

      <TableCell>
        <CategoryMark value={project.category} />
      </TableCell>

      <TableCell className="text-right tabular-nums text-slate-600">
        {project.estimated_days != null && `${project.estimated_days} jrs.`}
      </TableCell>

      {/* Delivered sits beside estimated so the two compare at a glance. A
          zero is not a value to read: a mission nobody has declared on stays
          empty. */}
      <TableCell className="text-right tabular-nums text-slate-600">
        {mission.delivered_days > 0 && `${mission.delivered_days} jrs.`}
      </TableCell>

      <TableCell>
        <MemberAvatars members={mission.leads} />
      </TableCell>

      <TableCell>
        <MemberAvatars members={mission.contributors} />
      </TableCell>
    </TableRow>
  );
}

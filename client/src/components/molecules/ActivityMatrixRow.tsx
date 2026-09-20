"use client";

import { ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";

import { MovementBadge } from "@/components/atoms/MovementBadge";
import { TableCell, TableRow } from "@/components/ui/table";
import type {
  ActivityLineResponse,
  ContributorResponse,
} from "@/lib/api/generated/model";
import { formatDays } from "@/lib/activity";
import { phaseDot, phaseLabel } from "@/lib/board";
import { STRONG_SEPARATOR } from "@/lib/table-frame";
import { formatShare } from "@/lib/statistics";

interface ActivityMatrixRowProps {
  line: ActivityLineResponse;
  contributors: ContributorResponse[];
  /** What the movement is measured against, named. */
  against: string;
  /** Opens the mission beside the reading, as the reference list does. */
  onOpen: (projectId: number) => void;
  /** Whether the line is a work package, drawn under its project. */
  isPackage?: boolean;
}

/**
 * One mission of the matrix, and the days each person booked against it.
 *
 * A project cut into work packages shows its total and folds them away: the
 * portfolio is what the screen reads, not the internal breakdown. Unfolded,
 * the project's own days read on the packages' own line — never the total a
 * second time.
 */
export function ActivityMatrixRow({
  line,
  contributors,
  against,
  onOpen,
  isPackage = false,
}: ActivityMatrixRowProps) {
  const [isOpen, setOpen] = useState(false);
  const packages = line.packages;

  return (
    <>
      <TableRow
        onClick={() => onOpen(line.project_id)}
        className="cursor-pointer bg-slate-50 hover:bg-slate-100"
      >
        <TableCell
          className={`sticky left-0 z-0 bg-white group-hover:bg-slate-50 ${
            isPackage ? "pl-8" : ""
          }`}
        >
          <span className="flex items-center gap-2">
            {packages.length > 0 ? (
              <button
                type="button"
                onClick={(event) => {
                  // Folding a project is not opening it.
                  event.stopPropagation();
                  setOpen(!isOpen);
                }}
                aria-expanded={isOpen}
                aria-label={`${isOpen ? "Replier" : "Déplier"} les lots de ${line.label}`}
                className="cursor-pointer text-slate-400 transition-colors hover:text-slate-700"
              >
                {isOpen ? (
                  <ChevronDown className="size-4" aria-hidden />
                ) : (
                  <ChevronRight className="size-4" aria-hidden />
                )}
              </button>
            ) : (
              <span className="size-4 shrink-0" aria-hidden />
            )}

            {line.status && (
              <span
                className={`size-2 shrink-0 rounded-full ${phaseDot(line.status)}`}
                title={phaseLabel(line.status)}
                aria-hidden
              />
            )}

            <span className={isPackage ? "text-slate-600" : "font-medium"}>
              {line.label}
            </span>

            {packages.length > 0 && !isOpen && (
              <span className="text-xs text-slate-400">
                {packages.length} lot{packages.length > 1 ? "s" : ""}
              </span>
            )}
          </span>
        </TableCell>

        {/* The reading comes before the detail: with twenty people across,
            the total would otherwise sit off the edge of the screen. */}
        <TableCell className="text-right font-medium tabular-nums">
          {formatDays(line.days)}
        </TableCell>
        <TableCell className="text-right tabular-nums text-slate-500">
          {formatShare(line.share)}
        </TableCell>
        <TableCell className={`text-right ${STRONG_SEPARATOR}`}>
          <MovementBadge days={line.movement} isNew={line.is_new} against={against} />
        </TableCell>

        {contributors.map((someone) => (
          <TableCell
            key={someone.id}
            className="text-center tabular-nums text-slate-700"
          >
            {formatDays(line.days_by_contributor[someone.id] ?? 0)}
          </TableCell>
        ))}
      </TableRow>

      {isOpen && (
        <>
          {/* The project's own days, told apart from what its packages
              carry: unfolded, the branch must not show its total twice. */}
          {line.own_days > 0 && (
            <ActivityMatrixRow
              line={{
                ...line,
                label: "Sans lot",
                days: line.own_days,
                days_by_contributor: line.own_days_by_contributor,
                packages: [],
              }}
              contributors={contributors}
              against={against}
              onOpen={onOpen}
              isPackage
            />
          )}
          {packages.map((each) => (
            <ActivityMatrixRow
              key={each.project_id}
              line={each}
              contributors={contributors}
              against={against}
              onOpen={onOpen}
              isPackage
            />
          ))}
        </>
      )}
    </>
  );
}

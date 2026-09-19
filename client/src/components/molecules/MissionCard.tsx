"use client";

import { CornerDownRight } from "lucide-react";

import { PriorityMark } from "@/components/atoms/PriorityMark";
import { phaseDot, phaseLabel } from "@/lib/board";
import { formatDecimalDays } from "@/lib/dates";
import type { HomeMission } from "@/lib/home";

interface MissionCardProps {
  mission: HomeMission;
  /** Opens the mission beside the screen. */
  onOpen: (projectId: number) => void;
}

/**
 * One of the missions one works on, as the home screen shows it.
 *
 * The same grammar as everywhere else — a coloured mark, then a label in
 * ordinary text — so that a mission read here and read on the board reads the
 * same way. It says where the mission stands and what one put on it this
 * month, and nothing about what it cost overall: that belongs to the reference
 * list, which is one click away.
 */
export function MissionCard({ mission, onOpen }: MissionCardProps) {
  const { project } = mission.item;

  return (
    <article
      onClick={(event) => {
        if ((event.target as HTMLElement).closest("button")) return;
        onOpen(project.id);
      }}
      className="group cursor-pointer rounded-lg border border-slate-300 bg-white p-3 shadow-xs transition-shadow hover:border-slate-500 hover:shadow-sm"
    >
      <h3 className="flex min-w-0 items-center gap-2 text-sm font-medium text-slate-900">
        {project.status && (
          <span
            aria-hidden
            title={phaseLabel(project.status)}
            className={`size-2 shrink-0 rounded-full ${phaseDot(project.status)}`}
          />
        )}
        <button
          type="button"
          onClick={() => onOpen(project.id)}
          className="cursor-pointer truncate text-left hover:underline"
        >
          {project.label}
        </button>
      </h3>

      {/* A work package's label names nothing on its own: « Lot 2 » is only a
          mission once one reads what it hangs from. */}
      {mission.parentLabel && (
        <p className="mt-1 flex min-w-0 items-center gap-1 text-xs text-slate-500">
          <CornerDownRight className="size-3 shrink-0" aria-hidden />
          <span className="truncate">{mission.parentLabel}</span>
        </p>
      )}

      <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-600">
        {project.status && <span>{phaseLabel(project.status)}</span>}
        {project.priority && (
          <span className="text-xs">
            <PriorityMark value={project.priority} />
          </span>
        )}
      </div>

      <p className="mt-2 text-xs tabular-nums text-slate-500">
        {mission.days > 0 ? (
          <>
            <span className="font-medium text-slate-900">
              {formatDecimalDays(mission.days)} j
            </span>{" "}
            ce mois-ci
          </>
        ) : (
          // Said plainly rather than left blank: a card with no figure would
          // read as a card whose figure failed to load.
          "Aucun temps saisi ce mois-ci"
        )}
      </p>
    </article>
  );
}

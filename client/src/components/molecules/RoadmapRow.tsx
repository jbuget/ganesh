"use client";

import { PlanBlockerNote } from "@/components/atoms/PlanBlockerNote";
import { PriorityMark } from "@/components/atoms/PriorityMark";
import { RoadmapBar } from "@/components/atoms/RoadmapBar";
import { TargetDateField } from "@/components/atoms/TargetDateField";
import type { RoadmapMissionResponse } from "@/lib/api/generated/model";
import { phaseDot, phaseLabel } from "@/lib/board";
import { slippageLabel } from "@/lib/planning";

interface RoadmapRowProps {
  mission: RoadmapMissionResponse;
  from: string;
  to: string;
  /** Opens the mission beside the drawing. */
  onOpen: (projectId: number) => void;
  /** Posts the date the mission is announced for. */
  onDate: (projectId: number, target: string | null) => void | Promise<void>;
}

/**
 * One line of the roadmap: what the mission is, and where it sits in time.
 *
 * The whole row opens the mission, as a row of the reference list does — one
 * reads a bar, wonders what is behind it, and the sheet comes to the side
 * without the drawing being lost. The one place that does not open it is the
 * date: posting a commitment is an act of its own, and it happens here.
 *
 * A work package is set in from its project, so a family reads as a family
 * without a band of its own.
 */
export function RoadmapRow({ mission, from, to, onOpen, onDate }: RoadmapRowProps) {
  const isWorkPackage = mission.kind === "work_package";

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label={`Ouvrir ${mission.label}`}
      onClick={() => onOpen(mission.project_id)}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onOpen(mission.project_id);
        }
      }}
      className="flex cursor-pointer items-center border-b border-slate-100 last:border-b-0 hover:bg-slate-50"
    >
      <div
        className={[
          "flex w-72 shrink-0 items-center gap-2 py-1.5 pr-3",
          isWorkPackage ? "pl-6" : "pl-3",
        ].join(" ")}
      >
        {mission.status && (
          <span
            aria-hidden
            title={phaseLabel(mission.status)}
            className={`size-2 shrink-0 rounded-full ${phaseDot(mission.status)}`}
          />
        )}

        <span
          title={mission.label}
          className="min-w-0 flex-1 truncate text-sm text-slate-800"
        >
          {mission.label}
        </span>

        <span className="shrink-0">
          <PriorityMark value={mission.priority} compact />
        </span>
      </div>

      {/* The date does not open the mission: it is the one act this screen
          carries, and a click meant for it must not be swallowed by the row. */}
      {/* The size is set here: a column of dates read at a glance is tighter
          than the same field on the single line of a sheet. */}
      <div
        className="w-36 shrink-0 pr-3 text-xs"
        onClick={(event) => event.stopPropagation()}
        onKeyDown={(event) => event.stopPropagation()}
        role="presentation"
      >
        <TargetDateField
          value={mission.target_date}
          missionLabel={mission.label}
          onChange={(target) => onDate(mission.project_id, target)}
        />
      </div>

      <div className="relative min-w-0 flex-1 pr-3">
        <RoadmapBar mission={mission} from={from} to={to} />

        {/* A mission with nothing to draw says why, where its bar would have
            been: an empty line reads as « rien à signaler », which is the
            opposite of what it means. */}
        {mission.segments.length === 0 && mission.blocker && (
          <span className="absolute top-1/2 left-0 -translate-y-1/2">
            <PlanBlockerNote reason={mission.blocker} />
          </span>
        )}
      </div>

      <div className="w-32 shrink-0 pr-3 text-right">
        {mission.is_late && mission.slippage_days !== null && (
          <span className="text-xs whitespace-nowrap text-red-600 tabular-nums">
            {slippageLabel(mission.slippage_days, true)}
          </span>
        )}
      </div>
    </div>
  );
}

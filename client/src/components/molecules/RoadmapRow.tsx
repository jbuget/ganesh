"use client";

import Link from "next/link";

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
  /** Posts the date the mission is announced for. */
  onDate: (projectId: number, target: string | null) => void | Promise<void>;
}

/**
 * One line of the roadmap: what the mission is, and where it sits in time.
 *
 * The name is a link and the bar is not: one goes to the sheet to act, and
 * stays here to read. A work package is set in from its project, so a family
 * reads as a family without a band of its own.
 */
export function RoadmapRow({ mission, from, to, onDate }: RoadmapRowProps) {
  const isWorkPackage = mission.kind === "work_package";

  return (
    <div className="flex items-center border-b border-slate-100 last:border-b-0 hover:bg-slate-50">
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

        <Link
          href={`/projects/${mission.project_id}`}
          title={mission.label}
          className="min-w-0 flex-1 cursor-pointer truncate text-sm text-slate-800 hover:underline"
        >
          {mission.label}
        </Link>

        <span className="shrink-0">
          <PriorityMark value={mission.priority} compact />
        </span>
      </div>

      <div className="w-36 shrink-0 pr-3">
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

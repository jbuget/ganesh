"use client";

import { ChevronRight } from "lucide-react";
import Link from "next/link";

import type { RecordedMissionResponse } from "@/lib/api/generated/model";
import { phaseDot, phaseLabel } from "@/lib/board";

interface UserMissionsProps {
  missions: RecordedMissionResponse[];
}

/**
 * The projects somebody is attached to.
 *
 * The mirror of the contributors on a project sheet: a project says who works
 * on it, and this says what one works on. Read from the assignments, which
 * state a team intention, and not from the time declared — what somebody was
 * put on and what they ended up doing are two different facts, and the second
 * one is read just below.
 *
 * Each row leads to the project rather than unfolding it: a project is steered
 * from its own sheet.
 */
export function UserMissions({ missions }: UserMissionsProps) {
  if (missions.length === 0) {
    return <p className="text-sm text-slate-400">Aucun projet</p>;
  }

  return (
    <ul className="space-y-0.5">
      {missions.map((mission) => (
        <li key={mission.project_id}>
          <Link
            href={`/projects/${mission.project_id}`}
            className="group flex cursor-pointer items-center gap-2 rounded px-1 py-1.5 transition-colors hover:bg-slate-50"
          >
            {mission.status && (
              <span
                aria-hidden
                className={`size-2.5 shrink-0 rounded-full ${phaseDot(mission.status)}`}
              />
            )}
            <span className="min-w-0 flex-1 truncate text-sm text-slate-700">
              {mission.label}
            </span>

            {/* Answering for a project is not the same as working on it, and
                the panel is where one looks to know which of the two. */}
            {mission.is_lead && (
              <span className="shrink-0 text-xs text-slate-400">Référent</span>
            )}

            {mission.status && (
              <span className="shrink-0 text-xs text-slate-500">
                {phaseLabel(mission.status)}
              </span>
            )}

            <ChevronRight
              aria-hidden
              className="size-4 shrink-0 text-slate-300 opacity-0 transition-opacity group-hover:opacity-100"
            />
          </Link>
        </li>
      ))}
    </ul>
  );
}

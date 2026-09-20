"use client";

import type { DeclaredWindowResponse } from "@/lib/api/generated/model";
import { formatDecimalDays } from "@/lib/dates";
import { windowLabel } from "@/lib/user-record";

interface UserDeclaredDaysProps {
  declared: DeclaredWindowResponse;
}

/**
 * Where somebody's time went lately, project by project.
 *
 * What one is put on and what one actually does are two different facts: the
 * projects above state the team's intention, this states what the register
 * holds. Read over a rolling window rather than the month running, which says
 * almost nothing when read on the 2nd.
 *
 * Off-project work is named as such rather than dropped: five days of which
 * three on leave is not a week spent the way the total alone suggests.
 */
export function UserDeclaredDays({ declared }: UserDeclaredDaysProps) {
  const span = windowLabel(declared.since, declared.until);

  if (declared.missions.length === 0) {
    return (
      <p className="text-sm text-slate-400">
        Aucun temps déclaré <span className="text-slate-300">{span}</span>
      </p>
    );
  }

  return (
    <div className="space-y-1.5">
      <p className="px-1 text-xs text-slate-400">{span}</p>

      <ul className="space-y-0.5">
        {declared.missions.map((mission) => {
          const part = declared.days > 0 ? (mission.days / declared.days) * 100 : 0;

          return (
            <li
              key={mission.project_id}
              className="flex items-center gap-2 px-1 py-1.5"
            >
              <span className="min-w-0 flex-1 truncate text-sm text-slate-700">
                {mission.label}
                {mission.is_off_project && (
                  <span className="ml-1.5 text-xs text-slate-400">hors projet</span>
                )}
              </span>

              <span
                aria-hidden
                className="hidden h-1.5 w-24 shrink-0 overflow-hidden rounded-full bg-slate-100 sm:block"
              >
                <span
                  className="block h-full rounded-full bg-sky-500"
                  style={{ width: `${part}%` }}
                />
              </span>

              <span className="w-16 shrink-0 text-right text-sm tabular-nums text-slate-600">
                {formatDecimalDays(mission.days)} j
              </span>
            </li>
          );
        })}
      </ul>

      <p className="flex items-baseline gap-2 border-t border-slate-200 px-1 pt-1.5 text-sm font-medium text-slate-700">
        <span className="min-w-0 flex-1">
          {declared.missions.length} projet{declared.missions.length > 1 ? "s" : ""}
        </span>
        <span className="shrink-0 tabular-nums">
          {formatDecimalDays(declared.days)} j
        </span>
      </p>
    </div>
  );
}

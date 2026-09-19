"use client";

import { Plus, UserRoundCheck } from "lucide-react";

/** A mission the team put someone on, as named by the reminder. */
interface AssignedMission {
  id: number;
  label: string;
}

interface AssignedMissionsCalloutProps {
  missions: AssignedMission[];
  onAdd: (projectId: number) => void;
}

/**
 * The gap between what the team assigned and what was entered.
 *
 * Contributors are settled week by week, in the team's own meetings; time is
 * declared month by month. Nothing brought the two together, and a mission one
 * was put on could go the whole month without a single row. This names the gap
 * — a suggestion, right next to the picker that answers it, and never a row of
 * its own: a row at zero would say « nothing done », which is not the same
 * thing as « not entered yet ».
 */
export function AssignedMissionsCallout({
  missions,
  onAdd,
}: AssignedMissionsCalloutProps) {
  if (missions.length === 0) return null;

  return (
    <aside
      role="status"
      className="mt-4 max-w-fit rounded-md border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700"
    >
      <p className="flex items-center gap-2">
        <UserRoundCheck className="size-4 shrink-0 text-slate-400" aria-hidden />
        Vous intervenez sur {missions.length}{" "}
        {missions.length > 1 ? "missions" : "mission"} sans temps déclaré ce mois-ci.
      </p>

      <ul className="mt-2 flex flex-wrap gap-1.5 pl-6">
        {missions.map((mission) => (
          <li key={mission.id}>
            <button
              type="button"
              aria-label={`Ajouter ${mission.label}`}
              onClick={() => onAdd(mission.id)}
              className="flex cursor-pointer items-center gap-1 rounded-md border border-slate-300 bg-white px-2 py-1 text-xs text-slate-700 transition-colors hover:border-slate-400 hover:bg-slate-100"
            >
              <Plus className="size-3 shrink-0 text-slate-400" aria-hidden />
              {mission.label}
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}

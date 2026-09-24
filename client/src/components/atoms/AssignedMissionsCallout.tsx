"use client";

import { Plus, UserRoundCheck } from "lucide-react";

/**
 * A line the reminder offers: a mission, and the trade to declare under.
 *
 * The trade rather than the mission alone, because a day is declared under an
 * activity: a button adding the mission would offer something the API refuses.
 */
interface AssignedMission {
  id: number;
  activityId: number | null;
  label: string;
  /** The mission above it, shown so two « Développement » read apart. */
  mission: string;
}

interface AssignedMissionsCalloutProps {
  missions: AssignedMission[];
  onAdd: (projectId: number, activityId: number | null) => void;
}

/**
 * The gap between what the team assigned and what was entered.
 *
 * Contributors are settled week by week, in the team's own meetings; time is
 * declared month by month. Nothing brought the two together, and a mission one
 * was put on could go the whole month without a single row. This names the gap
 * — a suggestion, read before the month it speaks of, and never a row of its
 * own: a row at zero would say « nothing done », which is not the same thing as
 * « not entered yet ».
 *
 * The sentence and the missions it names sit on one line: each mission is the
 * button that adds it, so reading the gap and closing it are the same gesture.
 *
 * Amber, the tone this application keeps for what one must know before writing
 * — a public holiday, an archived project, a colleague's month. But a light
 * amber, and the sentence itself in ordinary slate: nothing is wrong here, and
 * the note must not outshout the grid it sits above. Colour marks the buttons
 * and the icon, which is where the answer is. It never shows beside the other
 * amber banners: it only appears on one's own current month, which is exactly
 * when they do not.
 *
 * Full width, like the banners below it: a block that stops halfway across the
 * grid lines up with nothing.
 */
export function AssignedMissionsCallout({
  missions,
  onAdd,
}: AssignedMissionsCalloutProps) {
  if (missions.length === 0) return null;

  return (
    <aside
      role="status"
      className="mb-3 flex flex-wrap items-center gap-x-2 gap-y-1.5 rounded-md border border-amber-200 bg-amber-50 px-3 py-2.5 text-sm text-slate-700"
    >
      <UserRoundCheck className="size-4 shrink-0 text-amber-500" aria-hidden />

      <p>
        Vous êtes déclaré en tant qu&apos;intervenant sur {missions.length}{" "}
        {missions.length > 1 ? "projets" : "projet"} sans temps saisi ce mois-ci :
      </p>

      <ul className="flex flex-wrap gap-1.5">
        {missions.map((mission) => (
          <li key={`${mission.id}:${mission.activityId ?? ""}`}>
            <button
              type="button"
              aria-label={`Ajouter ${mission.mission} — ${mission.label}`}
              onClick={() => onAdd(mission.id, mission.activityId)}
              className="flex cursor-pointer items-center gap-1 rounded-md border border-amber-300 bg-white px-2 py-1 text-xs text-amber-900 transition-colors hover:border-amber-400 hover:bg-amber-100"
            >
              <Plus className="size-3 shrink-0 text-amber-500" aria-hidden />
              {mission.activityId === null
                ? mission.label
                : `${mission.mission} · ${mission.label}`}
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}

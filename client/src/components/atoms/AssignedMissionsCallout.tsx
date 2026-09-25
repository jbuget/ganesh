"use client";

import { Plus, UserRoundCheck } from "lucide-react";
import { useState } from "react";

import { ChooseActivityDialog } from "@/components/atoms/ChooseActivityDialog";

/**
 * A mission the reminder names, with the trades it may be declared under.
 *
 * One line per mission rather than per trade: the reminder says « you are on
 * this and have declared nothing », which is a fact about the mission. A
 * mission cut into three would otherwise repeat its name three times. Which
 * trade is asked at the moment of adding, and only when there is a choice.
 */
interface AssignedMission {
  id: number;
  label: string;
  /** Its open trades. Empty when nobody has cut the mission up yet. */
  activities: { id: number; label: string }[];
}

interface AssignedMissionsCalloutProps {
  missions: AssignedMission[];
  onAdd: (projectId: number, activityId: number) => void | Promise<void>;
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
  const [choosing, setChoosing] = useState<AssignedMission | null>(null);

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
          <li key={mission.id}>
            <button
              type="button"
              aria-label={`Ajouter ${mission.label}`}
              disabled={mission.activities.length === 0}
              title={
                mission.activities.length === 0
                  ? "Ce projet ne porte aucune activité : personne ne peut y déclarer de temps."
                  : undefined
              }
              onClick={() => {
                // Asked only when there is something to ask: a mission
                // carrying a single trade is added straight away, because a
                // dialog offering one button takes a click for nothing.
                if (mission.activities.length === 1) {
                  void onAdd(mission.id, mission.activities[0].id);
                } else {
                  setChoosing(mission);
                }
              }}
              className="flex cursor-pointer items-center gap-1 rounded-md border border-amber-300 bg-white px-2 py-1 text-xs text-amber-900 transition-colors hover:border-amber-400 hover:bg-amber-100 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Plus className="size-3 shrink-0 text-amber-500" aria-hidden />
              {mission.label}
            </button>
          </li>
        ))}
      </ul>

      {choosing && (
        <ChooseActivityDialog
          open
          onOpenChange={(isOpen) => !isOpen && setChoosing(null)}
          mission={choosing.label}
          activities={choosing.activities}
          onChoose={async (activityId) => {
            await onAdd(choosing.id, activityId);
            setChoosing(null);
          }}
        />
      )}
    </aside>
  );
}

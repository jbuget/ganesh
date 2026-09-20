import type { MissionShare } from "@/lib/activity";
import { formatDays } from "@/lib/activity";

interface ContributorMissionsProps {
  missions: MissionShare[];
  /** Days declared over the window, all missions together. */
  declaredDays: number;
}

/**
 * What one person put time on over the window, mission by mission.
 *
 * The « Par personne » table answers how much; this answers on what, without
 * making anyone cross back to the other tab and hunt their column across
 * twenty others.
 *
 * Off-project work is named as such rather than dropped: five days of which
 * three on leave is not a week spent the way the total alone suggests.
 */
export function ContributorMissions({
  missions,
  declaredDays,
}: ContributorMissionsProps) {
  if (missions.length === 0) {
    return <p className="text-slate-500">Aucun temps déclaré sur la période.</p>;
  }

  return (
    <div className="flex min-w-56 flex-col gap-1.5">
      <ul className="flex flex-col gap-1">
        {missions.map((mission) => (
          <li key={mission.projectId} className="flex items-baseline gap-4">
            <span className="min-w-0 flex-1 truncate">
              {mission.label}
              {mission.isOffProject && (
                <span className="ml-1.5 text-xs text-slate-400">hors projet</span>
              )}
            </span>
            <span className="shrink-0 tabular-nums">{formatDays(mission.days)}</span>
          </li>
        ))}
      </ul>

      <p className="flex items-baseline gap-4 border-t border-slate-200 pt-1.5 font-medium">
        <span className="min-w-0 flex-1">
          {missions.length} projet{missions.length > 1 ? "s" : ""}
        </span>
        <span className="shrink-0 tabular-nums">{formatDays(declaredDays)}</span>
      </p>
    </div>
  );
}

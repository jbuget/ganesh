import type { PhaseReachedResponse } from "@/lib/api/generated/model";
import { phaseDot } from "@/lib/board";
import { formatSpelledDate } from "@/lib/dates";

interface PhaseTimelineProps {
  phases: PhaseReachedResponse[];
}

/**
 * The steps a mission has passed, in order.
 *
 * Each date is named by what it completes — « Validé le 12 mai » — and
 * not by the phase being entered: that is how people talk about it.
 */
export function PhaseTimeline({ phases }: PhaseTimelineProps) {
  if (phases.length === 0) {
    return <p className="text-sm text-slate-400">Aucun passage enregistré</p>;
  }

  return (
    <ol aria-label="Étapes franchies" className="space-y-1.5">
      {phases.map((phase) => (
        <li key={phase.status} className="flex items-center gap-2 text-sm">
          <span
            aria-hidden
            className={`size-2 shrink-0 rounded-full ${phaseDot(phase.status)}`}
          />
          <span className="font-medium text-slate-700">{phase.label}</span>
          <span className="text-slate-500">
            le {formatSpelledDate(phase.reached_at)}
          </span>
        </li>
      ))}
    </ol>
  );
}

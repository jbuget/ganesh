import type { PhaseReachedResponse } from "@/lib/api/generated/model";
import { phaseDot } from "@/lib/board";

interface PhaseTimelineProps {
  phases: PhaseReachedResponse[];
}

/** Date en toutes lettres, abregee : « 17 sept. 2026 ». */
const MOIS = [
  "janv.",
  "févr.",
  "mars",
  "avr.",
  "mai",
  "juin",
  "juil.",
  "août",
  "sept.",
  "oct.",
  "nov.",
  "déc.",
];

function formatDate(iso: string): string {
  const [annee, month, day] = iso.split("-").map(Number);
  return `${day} ${MOIS[month - 1]} ${annee}`;
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
    <ol className="space-y-1.5">
      {phases.map((phase) => (
        <li key={phase.status} className="flex items-center gap-2 text-sm">
          <span
            aria-hidden
            className={`size-2 shrink-0 rounded-full ${phaseDot(phase.status)}`}
          />
          <span className="font-medium text-slate-700">{phase.label}</span>
          <span className="text-slate-500">le {formatDate(phase.reached_at)}</span>
        </li>
      ))}
    </ol>
  );
}

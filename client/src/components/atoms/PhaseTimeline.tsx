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
 * Les etapes franchies par une mission, dans l'ordre.
 *
 * Chaque date est nommee par ce qu'elle acheve — « Validé le 12 mai » — et non
 * par la phase ou l'on arrive : c'est ainsi qu'on en parle.
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

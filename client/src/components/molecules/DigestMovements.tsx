import { DigestFactLine } from "@/components/atoms/DigestFactLine";
import type { MovementKind, MovementResponse } from "@/lib/api/generated/model";
import { formatShortDate } from "@/lib/dates";
import { movementSentence } from "@/lib/gazette";

interface DigestMovementsProps {
  movements: MovementResponse[];
}

/**
 * The tint of each kind of movement.
 *
 * It follows what the fact means, not what it is about: a mise en service is
 * green wherever it appears, a step backwards amber. Anything that merely
 * happened stays slate — colour marks what deserves marking, and a list where
 * every line is coloured marks nothing.
 */
const DOTS: Record<MovementKind, string> = {
  project_created: "bg-sky-500",
  project_archived: "bg-slate-400",
  project_revived: "bg-sky-500",
  phase_advanced: "bg-slate-300",
  phase_stepped_back: "bg-amber-500",
  went_live: "bg-emerald-500",
  news_posted: "bg-slate-300",
  teammate_joined: "bg-violet-500",
  teammate_left: "bg-slate-400",
};

/**
 * Everything the month left in the register, in the order it happened.
 *
 * Nothing is summarised away: the chronology is what a digest is for, and the
 * tally above says how much of it there is before anyone starts reading.
 */
export function DigestMovements({ movements }: DigestMovementsProps) {
  return (
    <ul className="divide-y divide-slate-100">
      {movements.map((movement, rank) => (
        <DigestFactLine
          key={`${movement.at}-${movement.kind}-${movement.subject}-${rank}`}
          sentence={movementSentence(movement)}
          dot={DOTS[movement.kind] ?? "bg-slate-300"}
          when={formatShortDate(movement.at)}
        />
      ))}
    </ul>
  );
}

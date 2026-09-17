"use client";

import type { ProjectPriority } from "@/lib/api/generated/model";
import { priority } from "@/lib/board";

interface PriorityMarkProps {
  value: ProjectPriority | null | undefined;
}

/**
 * L'urgence d'une mission : une jauge coloree, un libelle ordinaire.
 *
 * Le remplissage de la jauge porte l'echelle autant que la teinte — quatre
 * barres, puis trois, deux, une — de sorte qu'elle se lise sans la couleur.
 */
export function PriorityMark({ value }: PriorityMarkProps) {
  const urgency = priority(value);
  if (!urgency) return null;

  const Icone = urgency.icon;

  return (
    <span className="flex items-center gap-1.5 text-slate-700">
      <Icone className={`size-4 shrink-0 ${urgency.colour}`} aria-hidden />
      {urgency.label}
    </span>
  );
}

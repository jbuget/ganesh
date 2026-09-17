"use client";

import type { ProjectPriority } from "@/lib/api/generated/model";
import { priorite } from "@/lib/board";

interface PriorityMarkProps {
  valeur: ProjectPriority | null | undefined;
}

/**
 * L'urgence d'une mission : une jauge coloree, un libelle ordinaire.
 *
 * Le remplissage de la jauge porte l'echelle autant que la teinte — quatre
 * barres, puis trois, deux, une — de sorte qu'elle se lise sans la couleur.
 */
export function PriorityMark({ valeur }: PriorityMarkProps) {
  const urgence = priorite(valeur);
  if (!urgence) return null;

  const Icone = urgence.icone;

  return (
    <span className="flex items-center gap-1.5 text-slate-700">
      <Icone className={`size-4 shrink-0 ${urgence.couleur}`} aria-hidden />
      {urgence.libelle}
    </span>
  );
}

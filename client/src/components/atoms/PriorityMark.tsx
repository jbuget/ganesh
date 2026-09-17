"use client";

import type { ProjectPriority } from "@/lib/api/generated/model";
import { priorite } from "@/lib/board";

interface PriorityMarkProps {
  valeur: ProjectPriority | null | undefined;
  /** Sans libelle, la marque tient dans une largeur de carte. */
  libelleVisible?: boolean;
}

/**
 * L'urgence d'une mission : une icone coloree, un libelle ordinaire.
 *
 * La forme porte l'echelle autant que la teinte — octogone d'alerte, double
 * chevron, tiret, chevron bas — de sorte qu'elle se lise sans la couleur.
 * Reduite a son icone, la marque garde son libelle pour les lecteurs d'ecran.
 */
export function PriorityMark({ valeur, libelleVisible = true }: PriorityMarkProps) {
  const urgence = priorite(valeur);
  if (!urgence) return null;

  const Icone = urgence.icone;

  return (
    <span
      className="flex items-center gap-1.5 text-slate-700"
      aria-label={
        libelleVisible ? undefined : `Priorité ${urgence.libelle.toLowerCase()}`
      }
    >
      <Icone
        className={`size-4 shrink-0 ${urgence.couleur}`}
        strokeWidth={urgence.trait}
        aria-hidden
      />
      {libelleVisible && urgence.libelle}
    </span>
  );
}

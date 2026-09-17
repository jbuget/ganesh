"use client";

import type { ProjectCategory } from "@/lib/api/generated/model";
import { categorie } from "@/lib/board";

interface CategoryMarkProps {
  valeur: ProjectCategory | null | undefined;
}

/**
 * L'axe strategique d'une mission : une puce coloree, un libelle ordinaire.
 *
 * Carree, la ou la pastille d'une phase est ronde : sur une meme ligne, deux
 * marques de meme forme se liraient comme la meme information.
 */
export function CategoryMark({ valeur }: CategoryMarkProps) {
  const axe = categorie(valeur);
  if (!axe) return null;

  return (
    <span className="flex items-center gap-1.5 text-slate-700">
      <span className={`size-2.5 shrink-0 rounded-[3px] ${axe.puce}`} aria-hidden />
      {axe.libelle}
    </span>
  );
}

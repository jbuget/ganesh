"use client";

import type { ProjectCategory } from "@/lib/api/generated/model";
import { category } from "@/lib/board";

interface CategoryMarkProps {
  value: ProjectCategory | null | undefined;
}

/**
 * L'axe strategique d'une mission : une puce coloree, un libelle ordinaire.
 *
 * Carree, la ou la pastille d'une phase est ronde : sur une meme ligne, deux
 * marques de meme forme se liraient comme la meme information.
 */
export function CategoryMark({ value }: CategoryMarkProps) {
  const axis = category(value);
  if (!axis) return null;

  return (
    <span className="flex items-center gap-1.5 text-slate-700">
      <span className={`size-2.5 shrink-0 rounded-[3px] ${axis.bullet}`} aria-hidden />
      {axis.label}
    </span>
  );
}

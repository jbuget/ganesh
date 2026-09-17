"use client";

import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { useCursorTooltip } from "@/lib/use-tooltip-curseur";

interface CardCounterProps {
  icon: LucideIcon;
  count: number;
  /** Ce que l'icone compte, au singulier puis au pluriel. */
  label: [string, string];
  /** Ce qu'annonce le lecteur d'ecran quand il n'y a rien a compter. */
  empty: string;
  /**
   * Ce que montre l'infobulle au survol — le dernier message, mis en forme.
   *
   * Il vient du parent et non d'ici : le rendu du markdown est un autre
   * composant, et un atom n'en compose aucun. Absent, le decompte se montre
   * sans infobulle.
   */
  apercu?: ReactNode;
}

/**
 * Un decompte en pied de carte : une icone, et un nombre quand il y en a un.
 *
 * L'icone reste en place a zero, sans nombre a cote : la carte garde la meme
 * forme d'une mission a l'autre, et l'absence se lit alors aussi vite qu'un
 * total. C'est le parti pris de Monday, dont les cartes nous servent de
 * reference.
 *
 * Quand le decompte annonce un fil, l'infobulle en donne le dernier message,
 * comme dans le referentiel : savoir qu'il y a trois messages ne dit pas s'il
 * faut les lire.
 */
export function CardCounter({
  icon: Icone,
  count,
  label,
  empty,
  apercu,
}: CardCounterProps) {
  const [singular, plural] = label;
  const { tooltip, follow, leave } = useCursorTooltip({ rich: true });

  return (
    <span
      aria-label={count === 0 ? empty : `${count} ${count > 1 ? plural : singular}`}
      onMouseMove={(event) => apercu && follow(event, apercu)}
      onMouseLeave={leave}
      className={`flex items-center gap-1 text-xs tabular-nums ${
        count === 0 ? "text-slate-300" : "text-slate-500"
      }`}
    >
      {count > 0 && count}
      <Icone className="size-3.5 shrink-0" aria-hidden />
      {tooltip}
    </span>
  );
}

"use client";

import { MessageCircle } from "lucide-react";
import type { ReactNode } from "react";

import { useTooltipCurseur } from "@/lib/use-tooltip-curseur";

interface UpdatesCounterProps {
  nombre: number;
  /**
   * Ce que montre l'infobulle au survol — le dernier message, mis en forme.
   *
   * Il vient du parent et non d'ici : le rendu du markdown est un autre
   * composant, et un atom n'en compose aucun. Absent, le decompte se montre
   * sans infobulle.
   */
  apercu?: ReactNode;
  /** Mene au fil lui-meme : l'apercu donne envie de repondre. */
  onOpen: () => void;
}

/**
 * Le fil de suivi d'une mission, en un nombre.
 *
 * Savoir qu'il y a trois messages ne dit pas s'il faut les lire : l'infobulle
 * donne le dernier en entier, ce qui epargne le plus souvent l'ouverture du
 * panneau. Quand elle ne suffit pas, le clic mene au fil lui-meme.
 *
 * Une mission sans mise a jour ne montre rien : dans un tableau, seul ce qui
 * se lit s'affiche.
 */
export function UpdatesCounter({ nombre, apercu, onOpen }: UpdatesCounterProps) {
  const { tooltip, suivre, quitter } = useTooltipCurseur({ riche: true });

  if (nombre === 0) return null;

  return (
    <button
      type="button"
      aria-label={`${nombre} ${nombre > 1 ? "mises à jour" : "mise à jour"}`}
      // La ligne entiere ouvre deja la mission : sans arret, le clic
      // l'ouvrirait deux fois, et la seconde sur le mauvais onglet.
      onClick={(event) => {
        event.stopPropagation();
        onOpen();
      }}
      onMouseMove={(event) => apercu && suivre(event, apercu)}
      onMouseLeave={quitter}
      className="inline-flex cursor-pointer items-center gap-1 rounded px-1 py-0.5 text-xs tabular-nums text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
    >
      {nombre}
      <MessageCircle className="size-3.5 shrink-0" aria-hidden />
      {tooltip}
    </button>
  );
}

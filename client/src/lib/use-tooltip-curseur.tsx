"use client";

import { useState, type MouseEvent, type ReactNode } from "react";
import { createPortal } from "react-dom";

/** Decalage de l'infobulle par rapport au curseur, pour ne pas le masquer. */
const OFFSET = { x: 14, y: 18 };

/**
 * Infobulle sombre qui suit le curseur.
 *
 * Elle parait des le survol, la ou l'infobulle native du navigateur se fait
 * attendre une seconde, et elle est montee dans un portail sur `body` : rendue
 * a l'interieur d'une cellule `sticky`, qui porte son propre contexte
 * d'empilement, elle passait sous la cellule de la ligne suivante et se
 * trouvait rognee.
 *
 * Le contenu est donne au survol et non a l'appel : une meme infobulle sert
 * ainsi plusieurs elements voisins, comme les pastilles d'intervenants.
 */
export function useTooltipCurseur() {
  const [etat, setEtat] = useState<{ x: number; y: number; contenu: ReactNode } | null>(
    null,
  );

  const tooltip = etat
    ? createPortal(
        <span
          role="tooltip"
          style={{ left: etat.x + OFFSET.x, top: etat.y + OFFSET.y }}
          className="pointer-events-none fixed z-50 rounded-md bg-slate-800 px-2.5 py-1.5 text-xs whitespace-nowrap text-white shadow-lg"
        >
          {etat.contenu}
        </span>,
        document.body,
      )
    : null;

  return {
    tooltip,
    suivre: (event: MouseEvent, contenu: ReactNode) =>
      setEtat({ x: event.clientX, y: event.clientY, contenu }),
    quitter: () => setEtat(null),
  };
}

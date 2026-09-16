"use client";

import { useState } from "react";
import { createPortal } from "react-dom";

import { formatTotal } from "@/lib/dates";

interface MissionLabelProps {
  label: string;
  consommeJ: number;
  estimeJ: number | null;
}

/** Decalage de l'infobulle par rapport au curseur, pour ne pas le masquer. */
const OFFSET = { x: 14, y: 18 };

/**
 * Libelle d'une mission, avec son avancement en infobulle.
 *
 * L'infobulle suit le curseur et est montee dans un portail sur `body` : rendue
 * a l'interieur de la cellule, qui est `sticky` et porte son propre contexte
 * d'empilement, elle passait sous la cellule sticky de la ligne suivante et se
 * trouvait rognee.
 *
 * Le nom peut etre tronque : l'infobulle le redonne en entier, accompagne du
 * consomme face a l'estime. Une seule infobulle porte les deux informations,
 * pour ne pas faire concurrence a l'infobulle native du navigateur.
 */
export function MissionLabel({ label, consommeJ, estimeJ }: MissionLabelProps) {
  const [position, setPosition] = useState<{ x: number; y: number } | null>(null);

  const tooltip = position ? (
    <span
      role="tooltip"
      style={{ left: position.x + OFFSET.x, top: position.y + OFFSET.y }}
      className="pointer-events-none fixed z-50 rounded-md bg-slate-800 px-2.5 py-1.5 text-xs whitespace-nowrap text-white shadow-lg"
    >
      <span className="font-medium">{label}</span>
      {estimeJ !== null && (
        <span className="ml-2 text-slate-300">
          {formatTotal(consommeJ)}/{estimeJ} jrs. estimés
        </span>
      )}
    </span>
  ) : null;

  return (
    <span
      className="flex items-center"
      onMouseMove={(event) => setPosition({ x: event.clientX, y: event.clientY })}
      onMouseLeave={() => setPosition(null)}
    >
      <span className="truncate">{label}</span>
      {tooltip && createPortal(tooltip, document.body)}
    </span>
  );
}

"use client";

import { formatJoursDecimal } from "@/lib/dates";
import { useTooltipCurseur } from "@/lib/use-tooltip-curseur";

interface MissionLabelProps {
  label: string;
  consommeJ: number;
  estimeJ: number | null;
}

/**
 * Libelle d'une mission, avec son avancement en infobulle.
 *
 * Le nom peut etre tronque : l'infobulle le redonne en entier, accompagne du
 * consomme face a l'estime. Une seule infobulle porte les deux informations,
 * pour ne pas faire concurrence a l'infobulle native du navigateur.
 */
export function MissionLabel({ label, consommeJ, estimeJ }: MissionLabelProps) {
  const { tooltip, suivre, quitter } = useTooltipCurseur();

  const contenu = (
    <>
      <span className="font-medium">{label}</span>
      {estimeJ !== null && (
        <span className="ml-2 text-slate-300">
          {formatJoursDecimal(consommeJ)}/{estimeJ} jrs. estimés
        </span>
      )}
    </>
  );

  return (
    <span
      className="flex items-center"
      onMouseMove={(event) => suivre(event, contenu)}
      onMouseLeave={quitter}
    >
      <span className="truncate">{label}</span>
      {tooltip}
    </span>
  );
}

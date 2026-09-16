import { formatTotal } from "@/lib/dates";

interface MissionLabelProps {
  label: string;
  consommeJ: number;
  estimeJ: number | null;
}

/**
 * Libelle d'une mission, avec son avancement en infobulle.
 *
 * Le nom peut etre tronque : l'infobulle le redonne en entier, accompagnee du
 * consomme face a l'estime. Une seule infobulle porte les deux informations,
 * pour ne pas faire concurrence a l'infobulle native du navigateur.
 */
export function MissionLabel({ label, consommeJ, estimeJ }: MissionLabelProps) {
  return (
    <span className="group/mission relative flex items-center">
      <span className="truncate">{label}</span>

      <span
        role="tooltip"
        className="pointer-events-none absolute top-1/2 left-full z-30 ml-3 -translate-y-1/2 rounded-md bg-slate-800 px-2.5 py-1.5 text-xs whitespace-nowrap text-white opacity-0 shadow-lg transition-opacity duration-100 group-hover/mission:opacity-100"
      >
        <span className="font-medium">{label}</span>
        {estimeJ !== null && (
          <span className="ml-2 text-slate-300">
            {formatTotal(consommeJ)}/{estimeJ} jrs. estimés
          </span>
        )}
      </span>
    </span>
  );
}

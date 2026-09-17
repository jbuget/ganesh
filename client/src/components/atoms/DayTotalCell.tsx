import { formatDays } from "@/lib/dates";

/** Cote d'une cellule portant un trait fort plutot que le trait de grille. */
export type StrongSide = "right" | "bottom";

interface DayTotalCellProps {
  value: number;
  isOffDay: boolean;
  /** Un jour non ouvre se reduit a une bande, sauf s'il porte une saisie. */
  isNarrow?: boolean;
  strongSides?: StrongSide[];
}

/**
 * Total d'une journee, toutes missions confondues.
 *
 * Le fond porte l'etat de la journee : verte si elle est complete, rouge si
 * elle ne l'est pas — qu'il manque du temps ou qu'il y en ait trop. C'est la
 * lecture utile au quotidien : reperer d'un coup d'oeil les journees a corriger.
 */
function backgroundFor(value: number, isOffDay: boolean) {
  if (value > 0) {
    return value === 1 ? "bg-emerald-100 text-emerald-900" : "bg-red-100 text-red-800";
  }
  if (isOffDay) return "bg-slate-100 text-slate-500";
  return "bg-white";
}

export function DayTotalCell({
  value,
  isOffDay,
  isNarrow = false,
  strongSides = [],
}: DayTotalCellProps) {
  const strong = new Set(strongSides);
  const isIncomplete = value > 0 && value !== 1;

  return (
    <td
      data-alert={isIncomplete ? "true" : undefined}
      className={[
        "h-9 border-r border-b text-center text-sm font-medium",
        isNarrow ? "w-2.5" : "w-9",
        strong.has("right") ? "border-r-slate-500" : "border-r-slate-300",
        strong.has("bottom") ? "border-b-slate-500" : "border-b-slate-300",
        backgroundFor(value, isOffDay),
      ].join(" ")}
    >
      {formatDays(value)}
    </td>
  );
}

"use client";

import { cycleDayValue, type DayValue } from "@/lib/day-value";
import { formatDays } from "@/lib/dates";

interface DayCellProps {
  value: DayValue;
  isOffDay: boolean;
  isFuture: boolean;
  isReadOnly: boolean;
  /** La derniere ligne ferme le tableau : son trait bas est le trait fort. */
  isLastRow?: boolean;
  /** La derniere colonne de jours porte le trait qui la separe des totaux. */
  isLastDay?: boolean;
  label: string;
  onChange: (next: DayValue) => void;
}

/**
 * Cellule unitaire de la matrice.
 *
 * Les bordures sont portees par le `<td>`, jamais par le bouton : le bouton se
 * dessinerait par-dessus le trait.
 *
 * Les jours non ouvres sont grises et verrouilles, les jours a venir attenues :
 * les premiers pour eviter les saisies par erreur, les seconds parce qu'ils
 * relevent du previsionnel et non du realise. Le jour courant n'est signale que
 * dans l'en-tete de colonne, pour ne pas charger la grille.
 */
export function DayCell({
  value,
  isOffDay,
  isFuture,
  isReadOnly,
  isLastRow = false,
  isLastDay = false,
  label,
  onChange,
}: DayCellProps) {
  // Un jour non ouvre ne se saisit jamais. La regle est portee par le domaine,
  // le verrouillage de la cellule n'en est que le reflet.
  const isLocked = isReadOnly || isOffDay;

  const background =
    value > 0
      ? "bg-sky-100 font-medium text-sky-900"
      : isOffDay
        ? "bg-slate-100"
        : "bg-white";

  return (
    <td
      className={[
        "border-r border-b p-0",
        isLastDay ? "border-r-slate-500" : "border-r-slate-300",
        isLastRow ? "border-b-slate-500" : "border-b-slate-300",
      ].join(" ")}
    >
      <button
        type="button"
        aria-label={label}
        title={label}
        disabled={isLocked}
        onClick={() => onChange(cycleDayValue(value))}
        className={[
          "block h-9 w-9 text-sm transition-colors",
          background,
          isFuture && value > 0 ? "opacity-60" : "",
          isLocked ? "cursor-not-allowed" : "cursor-pointer hover:bg-sky-50",
        ].join(" ")}
      >
        {formatDays(value)}
      </button>
    </td>
  );
}

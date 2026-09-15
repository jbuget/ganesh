"use client";

import { formatDays } from "@/lib/dates";

/** Valeur saisissable pour une demi-journee ou une journee complete. */
export type DayValue = 0 | 0.5 | 1;

const NEXT_VALUE: Record<DayValue, DayValue> = { 0: 0.5, 0.5: 1, 1: 0 };

/** Fait tourner la valeur d'une cellule : vide -> demi -> pleine -> vide. */
export function cycleDayValue(current: DayValue): DayValue {
  return NEXT_VALUE[current];
}

interface DayCellProps {
  value: DayValue;
  isOffDay: boolean;
  isFuture: boolean;
  isToday: boolean;
  isReadOnly: boolean;
  label: string;
  onChange: (next: DayValue) => void;
}

/**
 * Cellule unitaire de la matrice.
 *
 * Les jours non ouvres et les jours a venir sont visuellement distincts : les
 * premiers pour eviter les saisies par erreur, les seconds parce qu'ils
 * relevent du previsionnel et non du realise.
 */
export function DayCell({
  value,
  isOffDay,
  isFuture,
  isToday,
  isReadOnly,
  label,
  onChange,
}: DayCellProps) {
  const background =
    value > 0
      ? "bg-sky-100 font-medium text-sky-900"
      : isOffDay
        ? "bg-slate-100"
        : "bg-white";

  return (
    <td className="p-0">
      <button
        type="button"
        aria-label={label}
        title={label}
        disabled={isReadOnly}
        onClick={() => onChange(cycleDayValue(value))}
        className={[
          "h-9 w-9 border-r border-b border-slate-200 text-sm transition-colors",
          background,
          isFuture && value > 0 ? "opacity-55" : "",
          isToday ? "ring-1 ring-inset ring-sky-500" : "",
          isReadOnly ? "cursor-not-allowed" : "cursor-pointer hover:bg-sky-50",
        ].join(" ")}
      >
        {formatDays(value)}
      </button>
    </td>
  );
}

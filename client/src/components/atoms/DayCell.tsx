"use client";

/** Valeur saisissable pour une demi-journee ou une journee complete. */
export type DayValue = 0 | 0.5 | 1;

const NEXT_VALUE: Record<DayValue, DayValue> = { 0: 0.5, 0.5: 1, 1: 0 };

/** Fait tourner la valeur d'une cellule : vide -> demi -> pleine -> vide. */
export function cycleDayValue(current: DayValue): DayValue {
  return NEXT_VALUE[current];
}

const LABELS: Record<DayValue, string> = { 0: "", 0.5: "½", 1: "1" };

interface DayCellProps {
  value: DayValue;
  isOffDay: boolean;
  isReadOnly: boolean;
  onChange: (next: DayValue) => void;
}

/** Cellule unitaire de la matrice de saisie. */
export function DayCell({ value, isOffDay, isReadOnly, onChange }: DayCellProps) {
  return (
    <button
      type="button"
      aria-label={`Saisie : ${LABELS[value] || "vide"}`}
      disabled={isReadOnly}
      onClick={() => onChange(cycleDayValue(value))}
      className={[
        "h-8 w-8 border text-sm",
        isOffDay ? "bg-slate-100 text-slate-400" : "bg-white",
        isReadOnly ? "cursor-not-allowed opacity-60" : "cursor-pointer",
      ].join(" ")}
    >
      {LABELS[value]}
    </button>
  );
}

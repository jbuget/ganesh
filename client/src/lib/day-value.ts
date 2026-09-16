/**
 * Valeur saisissable dans une cellule de la matrice.
 *
 * Ce type et son cycle sont de la logique metier, pas du rendu : les garder
 * dans un composant obligeait la page a importer un atome pour un simple type.
 */
export type DayValue = 0 | 0.5 | 1;

/** Vide -> pleine -> demi -> vide. La journee complete est le cas courant. */
const NEXT_VALUE: Record<DayValue, DayValue> = { 0: 1, 1: 0.5, 0.5: 0 };

/** Fait tourner la valeur d'une cellule au clic. */
export function cycleDayValue(current: DayValue): DayValue {
  return NEXT_VALUE[current];
}

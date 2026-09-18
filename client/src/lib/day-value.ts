/**
 * The value a grid cell can take.
 *
 * This type and its cycle are business logic, not rendering: keeping them in a
 * component forced the page to import an atom for a mere type.
 */
export type DayValue = 0 | 0.5 | 1;

/** Empty -> full -> half -> empty. A full day is the common case. */
const NEXT_VALUE: Record<DayValue, DayValue> = { 0: 1, 1: 0.5, 0.5: 0 };

/** Cycles a cell's value on click. */
export function cycleDayValue(current: DayValue): DayValue {
  return NEXT_VALUE[current];
}

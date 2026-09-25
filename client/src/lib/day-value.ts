/**
 * The value a grid cell can take, and how the grid says it.
 *
 * **Stored in days, read in hours.** The domain counts in days and so does
 * everything built on it — estimates, capacity, the roadmap, the Gazette — so
 * a quarter is `0.25` all the way down. But a day is entered two hours at a
 * time, and a cell of thirty-six pixels reads « 2 » far better than « 0,25 ».
 * The two units follow the two axes of the grid: a day is read across, in
 * hours; a month is read down, in days.
 *
 * This type and what reads it are business logic, not rendering: keeping them
 * in a component forced the page to import an atom for a mere type.
 */
export type DayValue = 0 | 0.25 | 0.5 | 0.75 | 1;

/** A working day, in hours. What a quarter is a quarter of. */
export const HOURS_IN_A_DAY = 8;

/** A number of days in hours: half a day is four of them. */
export function toHours(value: number): number {
  return value * HOURS_IN_A_DAY;
}

/**
 * Hours as a cell and a day total show them: « 2 », « 8 », « 12 ».
 *
 * A null value shows nothing: in the grid, an empty cell means « nothing
 * entered », and filling it with zeros would make the grid unreadable.
 *
 * Halves are kept rather than rounded away. No cell can hold one — the grid
 * takes quarters — but a total inherited from elsewhere might, and showing
 * « 3 » for three and a half would report a figure the register does not hold.
 */
export function formatHours(value: number): string {
  if (value === 0) return "";
  const hours = toHours(value);
  return Number.isInteger(hours) ? String(hours) : String(hours).replace(".", ",");
}

/**
 * The hours a key stands for, or `null` when the key means nothing here.
 *
 * One types what one reads: the cell shows « 4 » and the key is `4`. Only the
 * even hours are taken, because they are the only ones a day divides into —
 * `3` is refused rather than rounded, so nobody is told they entered
 * something they did not.
 */
export function valueForKey(key: string): DayValue | null {
  if (key === "Backspace" || key === "Delete") return 0;
  // A digit, tested as a character rather than through `Number`: a space reads
  // as zero there, and the space bar is what cycles the cell.
  if (!/^[0-9]$/.test(key)) return null;
  const hours = Number(key);
  if (hours % 2 !== 0 || hours > HOURS_IN_A_DAY) return null;
  return (hours / HOURS_IN_A_DAY) as DayValue;
}

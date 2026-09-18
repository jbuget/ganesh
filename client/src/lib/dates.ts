/** Date helpers for the monthly grid. */

const MONTH_NAMES = [
  "janvier",
  "février",
  "mars",
  "avril",
  "mai",
  "juin",
  "juillet",
  "août",
  "septembre",
  "octobre",
  "novembre",
  "décembre",
];

const WEEKDAY_INITIALS = ["D", "L", "M", "M", "J", "V", "S"];

/** First day of the month, in ISO format `YYYY-MM-DD`. */
export function firstDayOfMonth(year: number, month: number): string {
  return `${year}-${String(month).padStart(2, "0")}-01`;
}

/** Readable month label, for instance « septembre 2026 ». */
export function formatMonth(year: number, month: number): string {
  return `${MONTH_NAMES[month - 1]} ${year}`;
}

/** Previous month, handling the year boundary. */
export function previousMonth(year: number, month: number) {
  return month === 1 ? { year: year - 1, month: 12 } : { year, month: month - 1 };
}

/** Next month, handling the year boundary. */
export function nextMonth(year: number, month: number) {
  return month === 12 ? { year: year + 1, month: 1 } : { year, month: month + 1 };
}

/** Day number within the month, from an ISO date. */
export function dayNumber(isoDate: string): number {
  return Number(isoDate.slice(8, 10));
}

/** Initial of the weekday (L, M, M, J, V, S, D). */
export function weekdayInitial(isoDate: string): string {
  const [year, month, day] = isoDate.split("-").map(Number);
  return WEEKDAY_INITIALS[new Date(Date.UTC(year, month - 1, day)).getUTCDay()];
}

/**
 * Formats a number of days inside a cell: 1 → « 1 », 0.5 → « ½ ».
 *
 * A null value shows nothing: in the grid, an empty cell means « nothing
 * entered », and filling it with zeros would make the grid unreadable.
 */
export function formatDays(value: number): string {
  if (value === 0) return "";
  const full = Math.floor(value);
  const hasHalf = value % 1 !== 0;
  if (full === 0) return "½";
  return hasHalf ? `${full}½` : String(full);
}

/**
 * Formats a number of days inside a total: 0 → « 0 ».
 *
 * Unlike a cell, a null total is information: « 0 j réalisé » must not
 * show up blank.
 */
export function formatTotal(value: number): string {
  return value === 0 ? "0" : formatDays(value);
}

/**
 * A number of days in decimal: 7.5 → « 7,5 », 26 → « 26 ».
 *
 * The grid prefers « ½ », which fits a narrow cell. On a board card,
 * where what is consumed reads against a whole estimate, the decimal speaks
 * faster: « 7,5/20 » compares at a glance, « 7½/20 » does not.
 *
 * Formatted by hand rather than through `toLocaleString`: the server render and
 * the browser must produce the same string, without depending on the locale
 * data available on either side.
 */
export function formatDecimalDays(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1).replace(".", ",");
}

/**
 * An ISO date as « 18/09/2026 ».
 *
 * Splits the string rather than going through `Date`: a naive timestamp read as
 * UTC would slip back a day in the evening, and the date shown would no longer
 * be the one the server recorded.
 */
export function formatDateCourte(iso: string): string {
  const [annee, month, day] = iso.slice(0, 10).split("-");
  return `${day}/${month}/${annee}`;
}

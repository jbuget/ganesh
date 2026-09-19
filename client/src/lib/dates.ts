/** Date helpers for the monthly grid. */

/** A month, as the screens point at one. */
export interface MonthCursor {
  year: number;
  month: number;
}

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

/** Abbreviated, for labels that must stay narrow: « 14 sept. ». */
const MONTH_ABBREVIATIONS = [
  "janv.",
  "févr.",
  "mars",
  "avr.",
  "mai",
  "juin",
  "juil.",
  "août",
  "sept.",
  "oct.",
  "nov.",
  "déc.",
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
export function previousMonth(year: number, month: number): MonthCursor {
  return month === 1 ? { year: year - 1, month: 12 } : { year, month: month - 1 };
}

/** Next month, handling the year boundary. */
export function nextMonth(year: number, month: number): MonthCursor {
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
export function formatShortDate(iso: string): string {
  const [year, month, day] = iso.slice(0, 10).split("-");
  return `${day}/${month}/${year}`;
}

/**
 * An ISO date spelled out and abbreviated: « 17 sept. 2026 ».
 *
 * Splits the string rather than going through `Date`, for the same reason
 * `formatShortDate` does: a naive timestamp read as UTC slips back a day.
 */
export function formatSpelledDate(iso: string): string {
  const [year, month, day] = iso.slice(0, 10).split("-").map(Number);
  return `${day} ${MONTH_ABBREVIATIONS[month - 1]} ${year}`;
}

/**
 * A week named by its Monday, without the year: « 14 sept. ».
 *
 * Twenty-six columns line up across a horizon: the year is the same on nearly
 * all of them, and repeating it would cost the width the days need.
 */
export function formatWeek(iso: string): string {
  const [, month, day] = iso.slice(0, 10).split("-").map(Number);
  return `${day} ${MONTH_ABBREVIATIONS[month - 1]}`;
}

/** The month a date falls in, spelled out: « septembre 2026 ». */
export function formatMonthOf(iso: string): string {
  const [year, month] = iso.slice(0, 10).split("-").map(Number);
  return formatMonth(year, month);
}

/**
 * Today, in ISO format, read from the local clock.
 *
 * Built by hand rather than through `toISOString`, which works in UTC: past
 * 22:00 in Paris it would already return tomorrow's date, and the grid would
 * dim a day that has not started.
 */
export function todayIso(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

/** A month as an address carries it: « 2026-08 ». */
export function monthParam(cursor: MonthCursor): string {
  return `${cursor.year}-${String(cursor.month).padStart(2, "0")}`;
}

/**
 * The month an address names, or null when it names none.
 *
 * An address is typed by hand and pasted between people: anything that is not
 * a month is ignored rather than trusted, and the screen falls back on the
 * month running.
 */
export function parseMonthParam(value: string | null): MonthCursor | null {
  if (!value || !/^\d{4}-\d{2}$/.test(value)) return null;

  const [year, month] = value.split("-").map(Number);
  return month >= 1 && month <= 12 ? { year, month } : null;
}

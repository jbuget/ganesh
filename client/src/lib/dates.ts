/** Utilitaires de dates pour la matrice mensuelle. */

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

/** Premier jour du mois, au format ISO `YYYY-MM-DD`. */
export function firstDayOfMonth(year: number, month: number): string {
  return `${year}-${String(month).padStart(2, "0")}-01`;
}

/** Libellé lisible du mois, par exemple « septembre 2026 ». */
export function formatMonth(year: number, month: number): string {
  return `${MONTH_NAMES[month - 1]} ${year}`;
}

/** Mois précédent, en gérant le passage d'année. */
export function previousMonth(year: number, month: number) {
  return month === 1 ? { year: year - 1, month: 12 } : { year, month: month - 1 };
}

/** Mois suivant, en gérant le passage d'année. */
export function nextMonth(year: number, month: number) {
  return month === 12 ? { year: year + 1, month: 1 } : { year, month: month + 1 };
}

/** Numéro du jour dans le mois, à partir d'une date ISO. */
export function dayNumber(isoDate: string): number {
  return Number(isoDate.slice(8, 10));
}

/** Initiale du jour de la semaine (L, M, M, J, V, S, D). */
export function weekdayInitial(isoDate: string): string {
  const [year, month, day] = isoDate.split("-").map(Number);
  return WEEKDAY_INITIALS[new Date(Date.UTC(year, month - 1, day)).getUTCDay()];
}

/** Formate un nombre de jours : 1 → « 1 », 0.5 → « ½ ». */
export function formatDays(value: number): string {
  if (value === 0) return "";
  const full = Math.floor(value);
  const hasHalf = value % 1 !== 0;
  if (full === 0) return "½";
  return hasHalf ? `${full}½` : String(full);
}

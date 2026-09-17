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

/**
 * Formate un nombre de jours dans une cellule : 1 → « 1 », 0.5 → « ½ ».
 *
 * Une valeur nulle ne s'affiche pas : dans la matrice, une cellule vide signifie
 * « rien de saisi », et la remplir de zéros rendrait la grille illisible.
 */
export function formatDays(value: number): string {
  if (value === 0) return "";
  const full = Math.floor(value);
  const hasHalf = value % 1 !== 0;
  if (full === 0) return "½";
  return hasHalf ? `${full}½` : String(full);
}

/**
 * Formate un nombre de jours dans un total : 0 → « 0 ».
 *
 * Contrairement à une cellule, un total nul est une information : « 0 j réalisé »
 * ne doit pas s'afficher comme un blanc.
 */
export function formatTotal(value: number): string {
  return value === 0 ? "0" : formatDays(value);
}

/**
 * Nombre de jours en decimal : 7.5 → « 7,5 », 26 → « 26 ».
 *
 * La matrice prefere « ½ », qui tient dans une cellule etroite. Sur une carte
 * de tableau, ou le consomme se lit face a un estime entier, le decimal parle
 * plus vite : « 7,5/20 » se compare d'un coup d'oeil, pas « 7½/20 ».
 *
 * Formate a la main plutot que par `toLocaleString` : le rendu serveur et le
 * navigateur doivent produire la meme chaine, sans dependre des donnees de
 * localisation disponibles de chaque cote.
 */
export function formatJoursDecimal(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1).replace(".", ",");
}

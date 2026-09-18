/** How long ago, spelled out and no more precise than it needs to be. */
const MINUTE = 60_000;
const HEURE = 60 * MINUTE;
const JOUR = 24 * HEURE;

/**
 * « a l'instant », « il y a 3 h », « le 11 sept. ».
 *
 * Past a week, the exact date says more than a number of days: one gets one's
 * bearings from « le 11 septembre », not from « il y a 23 jours ».
 */
export function depuis(iso: string, now: Date): string {
  const ecoule = now.getTime() - new Date(iso).getTime();

  if (ecoule < MINUTE) return "à l'instant";
  if (ecoule < HEURE) return `il y a ${Math.floor(ecoule / MINUTE)} min`;
  if (ecoule < JOUR) return `il y a ${Math.floor(ecoule / HEURE)} h`;
  if (ecoule < 7 * JOUR) {
    const days = Math.floor(ecoule / JOUR);
    return days === 1 ? "hier" : `il y a ${days} j`;
  }

  const MOIS = [
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
  const date = new Date(iso);
  return `le ${date.getDate()} ${MOIS[date.getMonth()]}`;
}

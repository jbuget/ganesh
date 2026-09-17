/** Depuis quand, en toutes lettres et sans precision inutile. */
const MINUTE = 60_000;
const HEURE = 60 * MINUTE;
const JOUR = 24 * HEURE;

/**
 * « a l'instant », « il y a 3 h », « le 11 sept. ».
 *
 * Au-dela d'une semaine, la date exacte dit plus que le nombre de jours : on
 * se repere a « le 11 septembre », pas a « il y a 23 jours ».
 */
export function depuis(iso: string, maintenant: Date): string {
  const ecoule = maintenant.getTime() - new Date(iso).getTime();

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

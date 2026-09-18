/** How long ago, spelled out and no more precise than it needs to be. */
const MINUTE = 60_000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

/**
 * « a l'instant », « il y a 3 h », « le 11 sept. ».
 *
 * Past a week, the exact date says more than a number of days: one gets one's
 * bearings from « le 11 septembre », not from « il y a 23 jours ».
 */
export function since(iso: string, now: Date): string {
  const elapsed = now.getTime() - new Date(iso).getTime();

  if (elapsed < MINUTE) return "à l'instant";
  if (elapsed < HOUR) return `il y a ${Math.floor(elapsed / MINUTE)} min`;
  if (elapsed < DAY) return `il y a ${Math.floor(elapsed / HOUR)} h`;
  if (elapsed < 7 * DAY) {
    const days = Math.floor(elapsed / DAY);
    return days === 1 ? "hier" : `il y a ${days} j`;
  }

  const MONTH = [
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
  return `le ${date.getDate()} ${MONTH[date.getMonth()]}`;
}

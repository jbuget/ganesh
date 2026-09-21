/**
 * An instant, read on the Paris clock.
 *
 * The API records *when* something was done and says so in UTC, zone
 * included: `2026-09-20T21:30:00+00:00`. What hour that names is the reader's
 * business, and the reader is a French team — so every instant this
 * application shows is turned into Paris time here, and nowhere else.
 *
 * Not the browser's own zone: a teammate reading from Montréal must see the
 * hour the gesture was made at in the office, not the one it was night at
 * where they are. A log that changes with the reader's flight is not a log.
 *
 * A *day* is not an instant. `entries.day`, `go_live_date` and their like
 * arrive as `YYYY-MM-DD`, carry no hour and need no zone: `lib/dates.ts`
 * reads those by splitting the string, which is right and stays right.
 */

/** The zone the team lives in, and the only one anything is shown in. */
export const PARIS = "Europe/Paris";

// Composed by hand from the parts rather than left to a locale: the server
// render and the browser must produce the same string, without depending on
// the locale data available on either side.
const PARIS_PARTS = new Intl.DateTimeFormat("en-GB", {
  timeZone: PARIS,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});

interface ParisParts {
  year: string;
  month: string;
  day: string;
  hour: string;
  minute: string;
}

function parisParts(iso: string): ParisParts {
  const parts = PARIS_PARTS.formatToParts(new Date(iso));
  const read = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((part) => part.type === type)?.value ?? "";
  return {
    year: read("year"),
    month: read("month"),
    day: read("day"),
    hour: read("hour"),
    minute: read("minute"),
  };
}

/**
 * The day an instant falls on in Paris, as `YYYY-MM-DD`.
 *
 * What `lib/dates.ts` then spells out. Slicing the raw string instead would
 * name the UTC day, and a gesture made at half past midnight would be filed
 * under the evening before.
 */
export function parisDay(iso: string): string {
  const { year, month, day } = parisParts(iso);
  return `${year}-${month}-${day}`;
}

/** The time of day in Paris: « 23:30 ». */
export function formatParisTime(iso: string): string {
  const { hour, minute } = parisParts(iso);
  return `${hour}:${minute}`;
}

/** A full instant in Paris: « 21/09/2026 à 23:30 ». */
export function formatParisDateTime(iso: string): string {
  const { year, month, day, hour, minute } = parisParts(iso);
  return `${day}/${month}/${year} à ${hour}:${minute}`;
}

/**
 * A full instant, said the way one says it: « 20/05/2026 à 13h35 ».
 *
 * The same moment as `formatParisDateTime`, spoken rather than read off a
 * clock face. It signs a gesture inside a sentence — « Téléversé par Alice
 * Chen le 20/05/2026 à 13h35 » — where a colon would read as a timestamp
 * dropped into prose.
 */
export function formatParisMoment(iso: string): string {
  const { year, month, day, hour, minute } = parisParts(iso);
  return `${day}/${month}/${year} à ${hour}h${minute}`;
}

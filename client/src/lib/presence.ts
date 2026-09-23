/**
 * Where somebody is each day of an ordinary week, said in French.
 *
 * Nothing here feeds a figure: not a coverage, not a capacity, not a number of
 * days expected. It answers one question — « est-ce que Léa est là mardi, et
 * est-elle au bureau ? » — and answering it is all it does.
 *
 * What is never asked for, anywhere, is *why* somebody works from home on
 * Wednesdays.
 */
import type { DayPresence, WeekPresenceResponse } from "@/lib/api/generated/model";

export interface Weekday {
  /** The field the API carries it under. */
  key: "monday" | "tuesday" | "wednesday" | "thursday" | "friday";
  label: string;
}

/** Monday first, as a week is read. The week stops on Friday. */
export const WEEKDAYS: readonly Weekday[] = [
  { key: "monday", label: "Lundi" },
  { key: "tuesday", label: "Mardi" },
  { key: "wednesday", label: "Mercredi" },
  { key: "thursday", label: "Jeudi" },
  { key: "friday", label: "Vendredi" },
];

export type WeekPresence = Record<Weekday["key"], DayPresence>;

/**
 * What a day is, said as somebody would say it.
 *
 * « Sur site » rather than « au bureau »: it is the word the team already uses
 * for the place, and one word for one thing.
 */
const SAID: Record<DayPresence, string> = {
  ON_SITE: "sur site",
  REMOTE: "télétravail",
  AWAY: "absent",
};

/** The order a click walks through: on site, remotely, away, and round again. */
const NEXT: Record<DayPresence, DayPresence> = {
  ON_SITE: "REMOTE",
  REMOTE: "AWAY",
  AWAY: "ON_SITE",
};

/** At the office unless said otherwise — the common case. */
export const AT_THE_OFFICE: WeekPresence = {
  monday: "ON_SITE",
  tuesday: "ON_SITE",
  wednesday: "ON_SITE",
  thursday: "ON_SITE",
  friday: "ON_SITE",
};

export function sayDay(day: DayPresence): string {
  return SAID[day];
}

export function nextDay(day: DayPresence): DayPresence {
  return NEXT[day];
}

/** The declared week, or a week at the office to start from when none was. */
export function weekOf(
  presence: WeekPresenceResponse | null | undefined,
): WeekPresence {
  if (!presence) return AT_THE_OFFICE;
  return {
    monday: presence.monday,
    tuesday: presence.tuesday,
    wednesday: presence.wednesday,
    thursday: presence.thursday,
    friday: presence.friday,
  };
}

export function daysOnSite(week: WeekPresence): number {
  return WEEKDAYS.filter((day) => week[day.key] === "ON_SITE").length;
}

export function daysPresent(week: WeekPresence): number {
  return WEEKDAYS.filter((day) => week[day.key] !== "AWAY").length;
}

/** « 3 jours sur site », « 1 jour sur site », « aucun jour sur site ». */
export function sayWeek(week: WeekPresence): string {
  const onSite = daysOnSite(week);
  const present = daysPresent(week);
  if (present === 0) return "absent toute la semaine";
  if (onSite === 0) return `${present} jour${present > 1 ? "s" : ""} en télétravail`;
  return `${onSite} jour${onSite > 1 ? "s" : ""} sur site sur ${present}`;
}

/**
 * A week on site, shaped as the API returns it.
 *
 * Exported for the tests that build a `UserResponse`: everyone has a week, so
 * every fixture needs one, and repeating the seven fields in six files is how
 * they drift apart.
 */
export const A_WEEK_ON_SITE: WeekPresenceResponse = {
  ...AT_THE_OFFICE,
  days_on_site: 5,
  days_present: 5,
};

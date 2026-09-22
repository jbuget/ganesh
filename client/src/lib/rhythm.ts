/**
 * The rhythm somebody works, said in French.
 *
 * A rhythm is a motif — which days, and how much of each — and never just a
 * number: a public holiday falls on a day of the week, so whoever never works
 * on a Monday loses nothing to the lundi de Pentecôte. The API holds the five
 * days; the reader gets the sentence here.
 *
 * What is never asked for, anywhere, is *why* somebody works four days a week.
 */
import type {
  DeclareRhythmRequest,
  WorkRhythmResponse,
} from "@/lib/api/generated/model";
import { formatDecimalDays } from "@/lib/dates";

/** What one day of a motif may be worth. The values the grid itself holds. */
export const DAY_VALUES = [0, 0.5, 1] as const;

export type DayValue = (typeof DAY_VALUES)[number];

export interface Weekday {
  /** The field the API carries it under. */
  key: "monday" | "tuesday" | "wednesday" | "thursday" | "friday";
  label: string;
  /** The one letter a compact picker shows. */
  initial: string;
}

/** Monday first, as a week is read and as `date.weekday()` counts. */
export const WEEKDAYS: readonly Weekday[] = [
  { key: "monday", label: "Lundi", initial: "L" },
  { key: "tuesday", label: "Mardi", initial: "M" },
  { key: "wednesday", label: "Mercredi", initial: "M" },
  { key: "thursday", label: "Jeudi", initial: "J" },
  { key: "friday", label: "Vendredi", initial: "V" },
];

/** What a full week expects — what anyone who declared nothing is read as. */
export const FULL_TIME: WeekPattern = {
  monday: 1,
  tuesday: 1,
  wednesday: 1,
  thursday: 1,
  friday: 1,
};

export type WeekPattern = Record<Weekday["key"], number>;

export function patternOf(rhythm: WorkRhythmResponse | null | undefined): WeekPattern {
  if (!rhythm) return FULL_TIME;
  return {
    monday: rhythm.monday,
    tuesday: rhythm.tuesday,
    wednesday: rhythm.wednesday,
    thursday: rhythm.thursday,
    friday: rhythm.friday,
  };
}

export function daysPerWeek(pattern: WeekPattern): number {
  return WEEKDAYS.reduce((total, day) => total + pattern[day.key], 0);
}

/**
 * The next value a day takes when one clicks it: a full day, a half, nothing.
 *
 * Down rather than up, because a motif is read as the exception to a full
 * week: one opens the picker to take days off, not to add them.
 */
export function nextValue(value: number): DayValue {
  if (value >= 1) return 0.5;
  if (value >= 0.5) return 0;
  return 1;
}

/** « 4 jours par semaine », « 4,5 jours par semaine », « 1 jour par semaine ». */
export function formatRhythm(pattern: WeekPattern): string {
  const total = daysPerWeek(pattern);
  const plural = total >= 2 ? "jours" : "jour";
  return `${formatDecimalDays(total)} ${plural} par semaine`;
}

/** What one day of the motif is worth, said plainly. */
export function formatDayValue(value: number): string {
  if (value >= 1) return "journée entière";
  if (value >= 0.5) return "demi-journée";
  return "non travaillé";
}

/** The payload the API takes: the five days, and the day the motif opens on. */
export function toRequest(
  pattern: WeekPattern,
  effectiveFrom: string,
): DeclareRhythmRequest {
  return { ...pattern, effective_from: effectiveFrom };
}

/** The first of the month a day falls in, which a declaration opens on by default. */
export function firstOfMonth(day: Date): string {
  const month = `${day.getMonth() + 1}`.padStart(2, "0");
  return `${day.getFullYear()}-${month}-01`;
}

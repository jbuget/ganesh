/**
 * Reading the Synthèse d'activité: its windows, and how its figures are said.
 *
 * Retrospective and factual, where Planification is prospective: nothing on
 * this screen is placed or supposed, everything was declared.
 */
import type { ActivityLineResponse, PeriodRange } from "@/lib/api/generated/model";
import { NOTHING, formatPersonDays } from "@/lib/statistics";

/**
 * The windows the screen offers, anchored rather than rolling.
 *
 * Read on a Monday morning, « la semaine dernière » means Monday to Sunday.
 * The last seven days would cut the weekend in two and straddle two weeks,
 * which is not what anyone means when they ask how last week went.
 */
export const ACTIVITY_RANGES: { value: PeriodRange; label: string }[] = [
  { value: "this_week", label: "Cette semaine" },
  { value: "last_week", label: "La semaine dernière" },
  { value: "last_two_weeks", label: "Les deux dernières semaines" },
  { value: "this_month", label: "Ce mois-ci" },
  { value: "last_month", label: "Le mois dernier" },
];

/** The window the screen opens on: what a Monday-morning reading asks for. */
export const DEFAULT_ACTIVITY_RANGE: PeriodRange = "last_week";

/** Days, or an em dash: an empty cell is not a zero, it is nothing declared. */
export function formatDays(days: number): string {
  return days === 0 ? NOTHING : formatPersonDays(days);
}

/** Days gained or lost, signed. Nothing when the line did not move. */
export function formatMovement(days: number): string | null {
  if (days === 0) return null;
  // A true minus sign, not a hyphen: at this size the hyphen reads as a dash.
  return `${days < 0 ? "−" : "+"}${formatPersonDays(Math.abs(days))} j`;
}

/** Every mission of a branch, the project first then its packages. */
export function flatten(line: ActivityLineResponse): ActivityLineResponse[] {
  return [line, ...line.packages.flatMap(flatten)];
}

/**
 * How many missions a reading covers, work packages counted with their project.
 *
 * The portfolio is what the screen reads: a product cut into four lots is one
 * mission, here as everywhere else.
 */
export function countMissions(lines: ActivityLineResponse[]): number {
  return lines.length;
}

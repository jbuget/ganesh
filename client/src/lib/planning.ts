import type { PlanBlocker } from "@/lib/api/generated/model";

/**
 * Horizons on offer.
 *
 * Nothing shorter than a quarter — below that a plan says only what everyone
 * already knows — and nothing longer than a year: beyond it the diaries hold
 * no declared leave, so the capacity read there is imaginary.
 */
export const HORIZONS = [
  { months: 3, label: "3 mois" },
  { months: 6, label: "6 mois" },
  { months: 12, label: "12 mois" },
] as const;

export const DEFAULT_HORIZON = 6;

/**
 * Why a mission carries no projected date, said in the team's own words.
 *
 * Each one names what to do about it: a plan that only said « impossible »
 * would leave the reader to guess which lever to pull.
 */
const BLOCKERS: Record<PlanBlocker, { label: string; hint: string }> = {
  no_estimate: {
    label: "Sans estimation",
    hint: "Estimez le build pour la placer dans le plan",
  },
  no_assignee: {
    label: "Sans intervenant",
    hint: "Affectez au moins un contributeur",
  },
  nothing_left: {
    label: "Rien à replanifier",
    hint: "L'estimation est déjà consommée ou déjà prévue",
  },
  beyond_horizon: {
    label: "Au-delà de l'horizon",
    hint: "Elle ne tient pas dans la fenêtre regardée",
  },
};

export function blocker(value: PlanBlocker | null | undefined) {
  return value ? BLOCKERS[value] : null;
}

/** How a projected landing sits against the date the team announced. */
export type Slippage = "none" | "early" | "on-time" | "late";

/**
 * What the landing of a mission says, given what the server worked out.
 *
 * Lateness is not decided here: the server owns the threshold below which a
 * projection is not worth crying about, so a row's red mark and the tally at
 * the top of the screen can never disagree.
 */
export function slippage(days: number | null | undefined, isLate: boolean): Slippage {
  if (isLate) return "late";
  if (days === null || days === undefined) return "none";
  return days < 0 ? "early" : "on-time";
}

/** « 5 jours de retard », « 3 jours d'avance », « dans les temps ». */
export function slippageLabel(days: number, isLate: boolean): string {
  const count = Math.abs(days);
  const plural = count > 1 ? "jours" : "jour";
  if (isLate) return `${count} ${plural} de retard`;
  if (days < 0) return `${count} ${plural} d'avance`;
  return "Dans les temps";
}

/** How full a week is, from what is declared and what is projected on it. */
export function fillRatio(capacity: number, booked: number, projected: number): number {
  if (capacity <= 0) return 0;
  return (booked + projected) / capacity;
}

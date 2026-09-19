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
 * A day or two either side reads as on time.
 *
 * A projection is not a commitment: announcing « en retard d'un jour » would
 * make the screen cry wolf, and a plan nobody believes steers nothing.
 */
const TOLERANCE_DAYS = 2;

export function slippage(days: number | null | undefined): Slippage {
  if (days === null || days === undefined) return "none";
  if (days > TOLERANCE_DAYS) return "late";
  if (days < -TOLERANCE_DAYS) return "early";
  return "on-time";
}

/** « 5 jours de retard », « 3 jours d'avance », « dans les temps ». */
export function slippageLabel(days: number): string {
  if (Math.abs(days) <= TOLERANCE_DAYS) return "Dans les temps";
  const count = Math.abs(days);
  const plural = count > 1 ? "jours" : "jour";
  return days > 0 ? `${count} ${plural} de retard` : `${count} ${plural} d'avance`;
}

/** How full a week is, from what is declared and what is projected on it. */
export function fillRatio(capacity: number, booked: number, projected: number): number {
  if (capacity <= 0) return 0;
  return (booked + projected) / capacity;
}

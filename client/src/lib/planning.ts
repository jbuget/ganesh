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

/** A what-if: a queue to serve, and who carries what. */
export interface Scenario {
  horizonMonths: number;
  order: number[];
  staffing: Record<number, number[]>;
}

/**
 * The same scenario spelled the same way every time.
 *
 * Two scenarios are the same hypothesis whatever order their keys happen to
 * come in: a record built by clicking Alice then Bob must not read as
 * different from one loaded back from the database the other way round.
 */
function canonical(scenario: Scenario): string {
  const staffing = Object.keys(scenario.staffing)
    .map(Number)
    .sort((a, b) => a - b)
    .map((id) => `${id}:${[...scenario.staffing[id]].sort((a, b) => a - b).join(",")}`)
    .join("|");
  return `${scenario.horizonMonths}/${scenario.order.join(",")}/${staffing}`;
}

/** Whether two scenarios suppose exactly the same thing. */
export function sameScenario(left: Scenario, right: Scenario): boolean {
  return canonical(left) === canonical(right);
}

/** Whether a scenario supposes anything at all. */
export function supposesSomething(scenario: Scenario): boolean {
  return scenario.order.length > 0 || Object.keys(scenario.staffing).length > 0;
}

/**
 * Whether a week column opens a new month.
 *
 * Twenty-six columns of « 14 sept. » and one no longer knows what quarter one
 * is reading: the month is spelled out again on the week that opens it.
 */
export function opensMonth(weeks: string[], index: number): boolean {
  if (index === 0) return true;
  return weeks[index].slice(0, 7) !== weeks[index - 1].slice(0, 7);
}

/**
 * What the banner says about the scenario on screen.
 *
 * Composed here rather than in the component so it can be read back by a
 * test: a French label built at run time is invisible to the type checker,
 * and a rename that crosses it would go unnoticed until someone opened the
 * page.
 */
export function scenarioNotice(
  simulationName: string | null,
  hasUnsavedChanges: boolean,
): string {
  if (simulationName === null) {
    return "Hypothèse en cours : rien n'est enregistré. Enregistrez-la pour la retrouver, ou reportez-la sur la fiche du projet pour la rendre réelle.";
  }

  const drift = hasUnsavedChanges ? " · modifiée depuis son enregistrement" : "";
  return `Simulation « ${simulationName} »${drift}. Elle ne change rien au réel : pour arbitrer, changez la priorité et les intervenants sur la fiche du projet.`;
}

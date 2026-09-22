/**
 * Reading the Synthèse d'activité: its windows, and how its figures are said.
 *
 * Retrospective and factual, where Planification is prospective: nothing on
 * this screen is placed or supposed, everything was declared.
 */
import type {
  ActivityLineResponse,
  ActivitySummaryResponse,
  ContributorResponse,
  PeriodRange,
} from "@/lib/api/generated/model";
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

/**
 * What a movement is measured against, ready to follow « par rapport ».
 *
 * Named rather than left to « la période précédente »: a month still running
 * is compared against the same stretch of the one before, not against a whole
 * month, and a reader who assumes otherwise misreads every movement.
 *
 * The « à » is carried here, contracted, rather than written in the sentence:
 * « à le mois d\'avant » and « à les deux semaines » are what a sentence
 * built by concatenation produces, and neither the type checker nor a test
 * asserting on a figure ever sees them.
 */
export function comparedWith(range: PeriodRange): string {
  switch (range) {
    case "this_week":
      return "à la même période de la semaine précédente";
    case "last_week":
      return "à la semaine d\'avant";
    case "last_two_weeks":
      return "aux deux semaines d\'avant";
    case "this_month":
      return "à la même période du mois précédent";
    case "last_month":
      return "au mois d\'avant";
    default:
      return "à la période précédente";
  }
}

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

/** One mission somebody put time on, and how much. */
export interface MissionShare {
  projectId: number;
  label: string;
  days: number;
  isOffProject: boolean;
}

/**
 * What one person put time on over the window, heaviest first.
 *
 * Read on the rolled-up lines, as the « Projets » count beside it is: four
 * packages of one product are one mission everywhere else on the screen, and
 * a breakdown that split them would contradict the figure it sits next to.
 *
 * Off-project work is in, and flagged rather than dropped: someone at 5 days
 * of which 3 on leave has not spent their week the way the bare total
 * suggests.
 */
export function missionsOf(
  summary: ActivitySummaryResponse,
  contributorId: number,
): MissionShare[] {
  return [
    ...ranked(summary.projects, contributorId, false),
    // After the missions, never mixed in among them: leave and training are
    // declared time, but they are not what the week was spent building.
    ...ranked(summary.off_project, contributorId, true),
  ];
}

function ranked(
  lines: ActivityLineResponse[],
  contributorId: number,
  isOffProject: boolean,
): MissionShare[] {
  return lines
    .map((line) => share(line, contributorId, isOffProject))
    .filter((mission) => mission.days > 0)
    .sort((a, b) => b.days - a.days || a.label.localeCompare(b.label, "fr"));
}

function share(
  line: ActivityLineResponse,
  contributorId: number,
  isOffProject: boolean,
): MissionShare {
  return {
    projectId: line.project_id,
    label: line.label,
    days: line.days_by_contributor[contributorId] ?? 0,
    isOffProject,
  };
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

/**
 * Teammates the window expected something of, who declared nothing.
 *
 * Whoever the window expects nothing of is left out rather than named here.
 * Somebody on leave has declared nothing and owes nothing, and listing them
 * under « n'ont rien déclaré » would read as a reproach for an absence the
 * register was told about.
 */
export function silentContributors(contributors: ContributorResponse[]): string[] {
  return contributors
    .filter((someone) => someone.expected_days > 0 && someone.declared_days === 0)
    .map((someone) => someone.display_name);
}

/**
 * How many teammates the window expects nothing of at all.
 *
 * Counted rather than named: a rhythm says how much of a week somebody works
 * and never why, and this figure exists so that nobody is quietly forgotten
 * — a teammate away with no return declared shows in no coverage and holds
 * no capacity, and the count is what puts them back in plain sight.
 */
export function awayContributors(contributors: ContributorResponse[]): number {
  return contributors.filter((someone) => someone.expected_days === 0).length;
}

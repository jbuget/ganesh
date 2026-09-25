import { normalise } from "@/lib/search-text";
import type {
  ProjectListItemResponse,
  ProjectResponse,
} from "@/lib/api/generated/model";

/** Missions on offer for adding, sorted by nature. */
export interface AvailableMissions {
  /** What one contributes to: offered first, before the whole reference list. */
  mine: ProjectResponse[];
  projectMissions: ProjectResponse[];
  offProject: ProjectResponse[];
}

/**
 * The missions someone is a contributor on.
 *
 * Being a lead does not count: answering for a mission's choices and contacts
 * is not spending days on it. Only what one has one's hands in has time to
 * declare, so only that is read here.
 */
export function assignedMissionIds(
  missions: ProjectListItemResponse[],
  userId: number | null,
): number[] {
  if (userId === null) return [];
  return missions
    .filter((mission) => mission.contributors.some((member) => member.id === userId))
    .map((mission) => mission.project.id);
}

/**
 * The order a French reader looks a mission up in.
 *
 * The database sorts under its own collation, which files « Évènementiel »
 * after « Support » — past the end of the list, where nobody looks for it. The
 * order is therefore settled here, where the language is known.
 */
function byLabel(a: ProjectResponse, b: ProjectResponse): number {
  return a.label.localeCompare(b.label, "fr");
}

/**
 * Missions a user can still add to their grid.
 *
 * Those already there are ruled out: no two rows for the same mission. Those
 * one contributes to come apart from the rest: the reference list runs to
 * dozens of missions, and the handful one works on should not have to be found
 * among them. A mission belongs to one group only — offered twice, it would
 * read as two.
 *
 * This logic lives outside the component so it can be tested without depending
 * on how a menu renders.
 */
export function availableMissions(
  projects: ProjectResponse[],
  excludedIds: number[],
  assignedIds: number[],
): AvailableMissions {
  const available = projects.filter((p) => !excludedIds.includes(p.id));
  const mine = available.filter((p) => assignedIds.includes(p.id));
  const rest = available.filter((p) => !assignedIds.includes(p.id));
  return {
    mine: [...mine].sort(byLabel),
    projectMissions: rest.filter((p) => p.kind !== "off_project").sort(byLabel),
    offProject: rest.filter((p) => p.kind === "off_project").sort(byLabel),
  };
}

/**
 * Missions one contributes to, with nothing declared on them yet.
 *
 * The gap between what the team assigned and what was entered: it is only ever
 * a reminder, never a row. A row at zero would say « nothing done », which is
 * not the same thing as « not entered yet », and the grid must keep saying what
 * was declared and nothing else.
 */
/** A mission one contributes to, with the trades it may be declared under. */
export interface MissionToDeclare {
  projectId: number;
  projectLabel: string;
  /** Its open trades. Empty when nobody has cut the mission up yet. */
  activities: { id: number; label: string }[];
}

export function missionsToDeclare(
  missions: ProjectListItemResponse[],
  userId: number | null,
  displayedProjectIds: number[],
): MissionToDeclare[] {
  const assigned = assignedMissionIds(missions, userId);

  // Named by mission rather than by trade: the reminder says « you are on
  // this and have declared nothing », which is a fact about the mission. A
  // mission cut into three trades is one line here, not three repeating its
  // name — which trade is asked for at the moment of adding, and only when
  // there is actually a choice to make.
  return missions
    .filter(
      (mission) =>
        mission.project.is_active &&
        assigned.includes(mission.project.id) &&
        !displayedProjectIds.includes(mission.project.id),
    )
    .map((mission) => ({
      projectId: mission.project.id,
      projectLabel: mission.project.label,
      activities: (mission.activities ?? [])
        .filter((activity) => activity.is_active)
        .map((activity) => ({ id: activity.id, label: activity.label })),
    }));
}

/** A row one may add to the grid: a mission, and the trade it is booked under. */
export interface OfferedRow {
  projectId: number;
  activityId: number | null;
  /** What names the row: the activity, or the mission when it carries none. */
  label: string;
  /** The mission above it, shown beside the label so two « Développement »
   *  never read as the same line. */
  projectLabel: string;
  kind: ProjectResponse["kind"];
}

/** The key a displayed row is recognised by: a mission **and** a trade. */
export function rowKey(projectId: number, activityId: number | null): string {
  return `${projectId}:${activityId ?? ""}`;
}

/**
 * What the selector may offer, one line per trade.
 *
 * A mission is declared on through one of its activities, so it is the
 * activities that are offered — never the mission itself, which the API
 * would refuse. Off-project work is the exception and stands for itself.
 *
 * A mission carrying no activity yet offers nothing: there is nothing to
 * declare on until somebody cuts it up, and offering a line the write would
 * refuse is worse than offering none.
 */
export function offeredRows(
  missions: ProjectListItemResponse[],
  displayedRowKeys: string[],
): OfferedRow[] {
  const rows: OfferedRow[] = [];

  for (const mission of missions) {
    const project = mission.project;
    if (!project.is_active) continue;

    if (project.kind === "off_project") {
      rows.push({
        projectId: project.id,
        activityId: null,
        label: project.label,
        projectLabel: project.label,
        kind: project.kind,
      });
      continue;
    }

    for (const activity of mission.activities ?? []) {
      if (!activity.is_active) continue;
      rows.push({
        projectId: project.id,
        activityId: activity.id,
        label: activity.label,
        projectLabel: project.label,
        kind: project.kind,
      });
    }
  }

  return rows
    .filter((row) => !displayedRowKeys.includes(rowKey(row.projectId, row.activityId)))
    .sort(
      (a, b) =>
        a.projectLabel.localeCompare(b.projectLabel) || a.label.localeCompare(b.label),
    );
}

/** What the selector searches through: the mission and the trade, together. */
export function searchableRow(row: OfferedRow): string {
  return row.activityId === null ? row.label : `${row.projectLabel} ${row.label}`;
}

/**
 * Whether a row answers what is being typed.
 *
 * Read without case or accents, as every other search in the application is:
 * a search answering differently on two screens is two searches, and the
 * reader has no way of knowing which one they are using.
 *
 * It looks through the mission's name as well as the trade's. Matching the
 * trade alone found nothing for « Contrôle », every row being called
 * « Développement » or « Chefferie de projet ».
 */
export function rowAnswers(row: OfferedRow, query: string): boolean {
  const asked = normalise(query.trim());
  return asked === "" || normalise(searchableRow(row)).includes(asked);
}

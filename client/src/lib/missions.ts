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

/** The key a displayed row is recognised by: a mission **and** a trade. */
export function rowKey(projectId: number, activityId: number | null): string {
  return `${projectId}:${activityId ?? ""}`;
}

/** A mission the selector offers, with the trades still free on the month. */
export interface OfferedMission {
  projectId: number;
  projectLabel: string;
  kind: ProjectResponse["kind"];
  /**
   * Its trades not yet on the month. Empty for off-project work, which is
   * added as itself and carries none.
   */
  activities: { id: number; label: string }[];
}

/**
 * What the selector lists: missions, not trades.
 *
 * One searches for a mission — that is the name one knows — and chooses the
 * trade once the mission is found. Listing the pairs flat made every row read
 * « Développement » and buried the name being looked for.
 *
 * A mission whose every trade is already on the month drops out: there is
 * nothing left to add under it. So does one nobody has cut up, because a
 * mission carrying no activity cannot be declared on at all.
 */
export function offeredMissions(
  missions: ProjectListItemResponse[],
  displayedRowKeys: string[],
): OfferedMission[] {
  const offered: OfferedMission[] = [];

  for (const mission of missions) {
    const project = mission.project;
    if (!project.is_active) continue;

    if (project.kind === "off_project") {
      if (!displayedRowKeys.includes(rowKey(project.id, null))) {
        offered.push({
          projectId: project.id,
          projectLabel: project.label,
          kind: project.kind,
          activities: [],
        });
      }
      continue;
    }

    const free = (mission.activities ?? [])
      .filter(
        (activity) =>
          activity.is_active &&
          !displayedRowKeys.includes(rowKey(project.id, activity.id)),
      )
      .map((activity) => ({ id: activity.id, label: activity.label }))
      .sort((a, b) => a.label.localeCompare(b.label));

    if (free.length === 0) continue;

    offered.push({
      projectId: project.id,
      projectLabel: project.label,
      kind: project.kind,
      activities: free,
    });
  }

  return offered.sort((a, b) => a.projectLabel.localeCompare(b.projectLabel));
}

/** Whether a mission answers what is being typed, without case or accents. */
export function missionAnswers(mission: OfferedMission, query: string): boolean {
  const asked = normalise(query.trim());
  return asked === "" || normalise(mission.projectLabel).includes(asked);
}

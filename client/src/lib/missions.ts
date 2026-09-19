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
    mine,
    projectMissions: rest.filter((p) => p.kind !== "off_project"),
    offProject: rest.filter((p) => p.kind === "off_project"),
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
export function missionsToDeclare(
  missions: ProjectListItemResponse[],
  userId: number | null,
  displayedProjectIds: number[],
): ProjectResponse[] {
  const assigned = assignedMissionIds(missions, userId);
  return missions
    .map((mission) => mission.project)
    .filter(
      (project) =>
        assigned.includes(project.id) && !displayedProjectIds.includes(project.id),
    );
}

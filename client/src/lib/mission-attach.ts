import type { ProjectListItemResponse } from "@/lib/api/generated/model";

/**
 * Which missions may be dragged onto which, in the reference list.
 *
 * The rules are the server's, read on the screen rather than discovered on a
 * refusal: a gesture the API would turn away is a gesture the table does not
 * offer. What it cannot say — why — is said by the panel menu, which opens a
 * dialog on the refusal and explains it.
 */

/** Whether the mission may be picked up to become a slice of a project. */
export function canBeAttached(
  mission: ProjectListItemResponse,
  subProjects: number,
): boolean {
  const { kind, is_published: published } = mission.project;
  // Off-project work is not a slice of anything; a mission carrying packages
  // would open a third level; a published one would lose its catalogue card.
  return kind !== "off_project" && subProjects === 0 && !published;
}

/** Whether the mission dragged would land somewhere by being dropped here. */
export function canReceive(
  target: ProjectListItemResponse,
  dragged: ProjectListItemResponse | null,
): boolean {
  if (dragged === null) return false;
  // Only a project carries packages: the hierarchy stops at two levels.
  if (target.project.kind !== "project") return false;
  if (target.project.id === dragged.project.id) return false;
  // Already there: the drop would write what is already written.
  return dragged.project.parent_id !== target.project.id;
}

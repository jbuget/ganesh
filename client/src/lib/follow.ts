import { followProject, unfollowProject } from "@/lib/api/generated/projects/projects";

/**
 * Raises or lowers the mark the team keeps an eye on a mission by.
 *
 * One function for every screen that offers the click — the reference list,
 * the board, the panel — so that none of them reaches the two routes on its
 * own.
 */
export async function setFollowed(projectId: number, following: boolean) {
  await (following ? followProject(projectId) : unfollowProject(projectId));
}

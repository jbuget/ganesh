"use client";

import { useQueryClient } from "@tanstack/react-query";

import {
  changeUserRole,
  declareOwnRhythm,
  setUserActive,
  withdrawOwnRhythm,
  updateUserIdentity,
} from "@/lib/api/generated/users/users";
import type {
  Role,
  UpdateUserIdentityRequest,
  UserResponse,
} from "@/lib/api/generated/model";
import { useCurrentUser, useTeammates } from "@/lib/api/queries";
import { type WeekPattern, toRequest } from "@/lib/rhythm";
import { NO_USER_FILTER, filterUsers, type UserFilters } from "@/lib/user-filters";
import { NO_USER_SORT, sortUsers, type UserSort } from "@/lib/user-sort";

/**
 * State and actions of the teammates screen.
 *
 * As everywhere else, coordination lives in a hook so the component carries
 * only the rendering. Filtering and ordering are part of it, as on the mission
 * reference list: the screen receives the criteria and the order, and renders
 * the list already reduced and arranged, without having to know how.
 */
export function useUsersScreen(
  filters: UserFilters = NO_USER_FILTER,
  sorted: UserSort = NO_USER_SORT,
) {
  const queryClient = useQueryClient();
  const { user: me } = useCurrentUser();
  // The management screen always asks for everyone, and hides rather than
  // re-fetches: a panel opened by a link on a deactivated account must find it,
  // whatever the list is showing at that moment.
  const { teammates, isLoading } = useTeammates(true);

  const kept = filterUsers(teammates, filters);

  return {
    isLoading,
    isManager: me?.role === "MANAGER",
    // Nobody cuts off their own access: the account would be turned away on
    // the next request, and no one could reopen it from inside.
    meId: me?.id,

    // One reference instant per render: without it, two rows of the same list
    // would compare against two different « now ».
    now: new Date(),

    users: sortUsers(kept, sorted),

    /**
     * Teammates kept, and teammates one would see with no criterion.
     *
     * What one is compared against is the list without its criteria, not the
     * whole table: deactivated accounts are hidden until they are asked for, so
     * counting them in would promise rows that clearing the filters would not
     * bring back. Asking for them raises both numbers at once.
     */
    visible: kept.length,
    total: filterUsers(teammates, { ...NO_USER_FILTER, states: filters.states }).length,

    /** The teammate a panel is opened on, deactivated or not. */
    find: (userId: number) =>
      teammates.find((teammate) => teammate.id === userId) ?? null,

    async changeRole(userId: number, role: Role) {
      await changeUserRole(userId, { role });
      await queryClient.invalidateQueries();
    },

    /**
     * Who a teammate is, where they work, and where one finds them on GitHub.
     *
     * The four fields go to the API together — what is left out is emptied —
     * so a change to one carries the other three as they stand.
     */
    async updateIdentity(user: UserResponse, change: UpdateUserIdentityRequest) {
      await updateUserIdentity(user.id, {
        first_name: user.first_name ?? null,
        last_name: user.last_name ?? null,
        department: user.department ?? null,
        github_username: user.github_username ?? null,
        ...change,
      });
      await queryClient.invalidateQueries();
    },

    /**
     * One's own rhythm, and nobody else's.
     *
     * The route carries no teammate: there is no colleague this could reach
     * by mistake, which is the guarantee rather than a shorthand.
     */
    async declareOwnRhythm(pattern: WeekPattern, effectiveFrom: string) {
      await declareOwnRhythm(toRequest(pattern, effectiveFrom));
      await queryClient.invalidateQueries();
    },

    /**
     * One of one's own rhythms, taken back out.
     *
     * A history one may only add to is one nobody can correct: a rhythm
     * entered on the wrong date would hold its place for good.
     */
    async withdrawOwnRhythm(effectiveFrom: string) {
      await withdrawOwnRhythm(effectiveFrom);
      await queryClient.invalidateQueries();
    },

    async setActive(userId: number, is_active: boolean) {
      await setUserActive(userId, { is_active });
      await queryClient.invalidateQueries();
    },
  };
}

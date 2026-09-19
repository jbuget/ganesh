"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import {
  changeUserRole,
  setUserActive,
  updateUserIdentity,
} from "@/lib/api/generated/users/users";
import type {
  Role,
  UpdateUserIdentityRequest,
  UserResponse,
} from "@/lib/api/generated/model";
import { useCurrentUser, useTeammates } from "@/lib/api/queries";

/**
 * State and actions of the teammates screen.
 *
 * As everywhere else, coordination lives in a hook so the component carries
 * only the rendering.
 */
export function useUsersScreen() {
  const queryClient = useQueryClient();
  const { user: me } = useCurrentUser();
  const [withInactive, setWithInactive] = useState(false);
  // The management screen always asks for everyone, and hides rather than
  // re-fetches: a panel opened by a link on a deactivated account must find it,
  // whatever the list is showing at that moment.
  const { teammates, isLoading } = useTeammates(true);

  const visible = withInactive
    ? teammates
    : teammates.filter((teammate) => teammate.is_active);

  return {
    isLoading,
    isManager: me?.role === "MANAGER",
    // Nobody cuts off their own access: the account would be turned away on
    // the next request, and no one could reopen it from inside.
    meId: me?.id,
    withInactive,

    // One reference instant per render: without it, two rows of the same list
    // would compare against two different « now ».
    now: new Date(),

    toggleInactive: () => setWithInactive((current) => !current),

    /** By name, the only order one finds by eye in a team list. */
    users: [...visible].sort((a, b) =>
      a.display_name.localeCompare(b.display_name, "fr"),
    ),

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

    async setActive(userId: number, is_active: boolean) {
      await setUserActive(userId, { is_active });
      await queryClient.invalidateQueries();
    },
  };
}

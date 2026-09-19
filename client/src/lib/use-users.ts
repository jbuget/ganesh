"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { changeUserRole, setUserActive } from "@/lib/api/generated/users/users";
import type { Role } from "@/lib/api/generated/model";
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
  const { teammates, isLoading } = useTeammates(withInactive);

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
    users: [...teammates].sort((a, b) =>
      a.display_name.localeCompare(b.display_name, "fr"),
    ),

    async changeRole(userId: number, role: Role) {
      await changeUserRole(userId, { role });
      await queryClient.invalidateQueries();
    },

    async setActive(userId: number, is_active: boolean) {
      await setUserActive(userId, { is_active });
      await queryClient.invalidateQueries();
    },
  };
}

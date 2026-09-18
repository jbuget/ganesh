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
  const [avecInactifs, setAvecInactifs] = useState(false);
  const { teammates, isLoading } = useTeammates(avecInactifs);

  return {
    isLoading,
    isManager: me?.role === "MANAGER",
    //: Nobody cuts off their own access: the account would be turned away on
    //: the next request, and no one could reopen it from inside.
    moiId: me?.id,
    avecInactifs,

    // One reference instant per render: without it, two rows of the same list
    // would compare against two different « now ».
    maintenant: new Date(),

    basculerInactifs: () => setAvecInactifs((actuel) => !actuel),

    /** By name, the only order one finds by eye in a team list. */
    collaborateurs: [...teammates].sort((a, b) =>
      a.display_name.localeCompare(b.display_name, "fr"),
    ),

    async changerRole(userId: number, role: Role) {
      await changeUserRole(userId, { role });
      await queryClient.invalidateQueries();
    },

    async changerActivite(userId: number, is_active: boolean) {
      await setUserActive(userId, { is_active });
      await queryClient.invalidateQueries();
    },
  };
}

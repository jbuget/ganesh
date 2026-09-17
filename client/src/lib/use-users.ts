"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { changeUserRole } from "@/lib/api/generated/users/users";
import type { Role } from "@/lib/api/generated/model";
import { useCurrentUser, useTeammates } from "@/lib/api/queries";

/**
 * Etat et actions de l'ecran des collaborateurs.
 *
 * Comme partout ailleurs, la coordination vit dans un hook pour que le
 * composant ne porte que le rendu.
 */
export function useUsersScreen() {
  const queryClient = useQueryClient();
  const { user: me } = useCurrentUser();
  const [avecInactifs, setAvecInactifs] = useState(false);
  const { teammates, isLoading } = useTeammates(avecInactifs);

  return {
    isLoading,
    isManager: me?.role === "MANAGER",
    avecInactifs,

    // Un seul instant de reference par rendu : sans cela, deux lignes de la
    // meme liste se compareraient a deux « maintenant » differents.
    maintenant: new Date(),

    basculerInactifs: () => setAvecInactifs((actuel) => !actuel),

    /** Par nom, seul ordre qui se retrouve a l'oeil dans une liste d'equipe. */
    collaborateurs: [...teammates].sort((a, b) =>
      a.display_name.localeCompare(b.display_name, "fr"),
    ),

    async changerRole(userId: number, role: Role) {
      await changeUserRole(userId, { role });
      await queryClient.invalidateQueries();
    },
  };
}

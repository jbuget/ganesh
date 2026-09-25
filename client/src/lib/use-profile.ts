"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import type { ReminderCadence } from "@/lib/api/generated/model";
import { chooseOwnReminderCadence } from "@/lib/api/generated/users/users";
import { useCurrentUser } from "@/lib/api/queries";

/**
 * One's own profile: who one is, and how one wants to be written to.
 *
 * The route carries no teammate — `PUT /users/me/reminder-cadence` — so there
 * is no colleague's mailbox this screen could reach by mistake. That is the
 * guarantee rather than a shorthand, and it is why the screen takes no
 * identifier at all.
 */
export function useProfileScreen() {
  const { user, isLoading } = useCurrentUser();
  const queryClient = useQueryClient();
  const [isSaving, setSaving] = useState(false);

  return {
    user,
    isLoading,
    isSaving,

    /**
     * Says how often one wants the letter naming what is waiting.
     *
     * The whole cache is invalidated rather than the one query: the cadence
     * travels on `UserResponse`, which the sidebar and the teammate screens
     * also read, and a figure refreshed in one place only is a figure that
     * disagrees with itself.
     */
    async choose(cadence: ReminderCadence) {
      setSaving(true);
      try {
        await chooseOwnReminderCadence({ cadence });
        await queryClient.invalidateQueries();
      } finally {
        setSaving(false);
      }
    },
  };
}

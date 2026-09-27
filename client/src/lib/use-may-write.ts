"use client";

import { useCurrentUser } from "@/lib/api/queries";
import { canWrite } from "@/lib/roles";

/**
 * Whether the person reading may write into Ganesh.
 *
 * One reading, for the whole application: a guest reads every screen and
 * declares nothing into any of them, and a screen that worked that out for
 * itself would be a screen that could get it wrong.
 *
 * It is **false while the current user is still loading**, which is the
 * cautious way round: a gesture offered for a moment and then taken away is
 * worse than one that appears a beat late.
 *
 * It is false while an account is being borrowed, too, whatever the role
 * says. An administrator reading as a teammate is reading: the API refuses
 * every gesture on its side, and a screen that went on offering them would
 * have somebody click on a refusal.
 */
export function useMayWrite(): boolean {
  const { user } = useCurrentUser();
  return canWrite(user?.role) && !user?.impersonated_by;
}

/**
 * Whether the person reading is reading as somebody else.
 *
 * Beside `useMayWrite` rather than in a file of its own: it is the same
 * question asked of the same answer, and a screen reaching for
 * `useCurrentUser` to work it out is a screen that could get it wrong.
 */
export function useIsBorrowing(): boolean {
  const { user } = useCurrentUser();
  return Boolean(user?.impersonated_by);
}

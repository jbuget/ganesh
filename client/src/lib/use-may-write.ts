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
 */
export function useMayWrite(): boolean {
  const { user } = useCurrentUser();
  return canWrite(user?.role);
}

"use client";

import { MyRequestsPage } from "@/components/organisms/MyRequestsPage";
import { RequestsPage } from "@/components/organisms/RequestsPage";
import { useCurrentUser } from "@/lib/api/queries";

/**
 * The one address of the needs, read differently by the two sides of it.
 *
 * Whoever only comes to ask for something gets their own needs and the state
 * of each; the team gets the whole list and weighs it. One address rather
 * than two: a link to a need must open for everybody who may read it, and a
 * requester who was sent one must not land on a page saying « interdit ».
 */
export function RequestsScreen() {
  const { user } = useCurrentUser();

  if (!user) return null;
  return user.role === "REQUESTER" ? <MyRequestsPage /> : <RequestsPage />;
}

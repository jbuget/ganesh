"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useCurrentUser } from "@/lib/api/queries";

/**
 * Reading Ganesh as one of the team, and giving the account back.
 *
 * Two gestures, and both of them change who the whole application is for —
 * so both clear the cache before anything else is drawn. A screen kept from
 * the previous reader would be the one thing this feature must never do:
 * show an administrator a teammate's name over their own data, or the other
 * way round.
 *
 * Neither gesture calls the API: what they move is a sealed cookie, and only
 * a Route Handler can write one. The handler asks the API whether the
 * borrowing would be allowed before writing anything down, so a refusal here
 * leaves the reader exactly where they were.
 */
export function useReadAs() {
  const { user } = useCurrentUser();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [isMoving, setMoving] = useState(false);

  /** Who is reading, when it is not the account being read. */
  const borrower = user?.impersonated_by ?? null;

  async function go(to: string) {
    queryClient.clear();
    router.replace(to);
    router.refresh();
  }

  return {
    borrower,
    isBorrowing: borrower !== null,
    isMoving,

    /**
     * Opens a teammate's account. Administrators only, and the API says so.
     *
     * Lands on the home screen rather than staying where one was: half the
     * point is seeing what somebody reaches at all, and the screen one was on
     * may well be one they never see.
     */
    async readAs(userId: number): Promise<string | null> {
      setMoving(true);
      try {
        const response = await fetch("/api/auth/impersonate", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ userId }),
        });
        if (!response.ok) {
          const said = (await response.json().catch(() => null)) as {
            detail?: string;
          } | null;
          return said?.detail ?? "Ce compte ne peut pas être ouvert.";
        }
        await go("/");
        return null;
      } finally {
        setMoving(false);
      }
    },

    /** Gives the account back, and the administrator their own screens. */
    async giveBack() {
      setMoving(true);
      try {
        await fetch("/api/auth/impersonate", { method: "DELETE" });
        // Back to the team list: it is where one left from, and where one
        // goes next to look at somebody else.
        await go("/users");
      } finally {
        setMoving(false);
      }
    },
  };
}

"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

/**
 * End of session, as the browser sees it.
 *
 * The cookie goes server-side, but the screen keeps in memory what it has
 * already loaded: clearing the cache avoids showing again, even for a moment,
 * the data of someone who has just left.
 */
export function useSignOut(): () => Promise<void> {
  const router = useRouter();
  const queryClient = useQueryClient();

  return async function signOut() {
    await fetch("/api/auth/signout", { method: "POST" });
    queryClient.clear();
    router.replace("/");
    router.refresh();
  };
}

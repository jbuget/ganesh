"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

/**
 * Fin de session, vue du navigateur.
 *
 * Le cookie part cote serveur, mais l'ecran garde en memoire ce qu'il a deja
 * charge : vider le cache evite de reafficher, ne serait-ce qu'un instant, les
 * donnees de quelqu'un qui vient de partir.
 */
export function useDeconnexion(): () => Promise<void> {
  const router = useRouter();
  const queryClient = useQueryClient();

  return async function seDeconnecter() {
    await fetch("/api/auth/signout", { method: "POST" });
    queryClient.clear();
    router.replace("/");
    router.refresh();
  };
}

"use client";

import { useQueryClient } from "@tanstack/react-query";

import {
  useCreateShareLink,
  useRevokeShareLink,
} from "@/lib/api/generated/gazette/gazette";
import { useShareLinks } from "@/lib/api/queries";
import { sharedAddress } from "@/lib/gazette";

/**
 * The links that open one version of a digest, and the gestures on them.
 *
 * All the coordination lives here — listing, opening, closing, and saying
 * where a token is read — so the panel carries nothing but the rendering.
 */
export function useShare(month: string, version: number | null) {
  const queryClient = useQueryClient();
  const { links, isLoading } = useShareLinks(month, version);
  const create = useCreateShareLink();
  const revoke = useRevokeShareLink();

  return {
    links,
    isLoading,
    isOpening: create.isPending,

    /** Where the link is read, built from the address the team is on. */
    addressOf: (token: string) => sharedAddress(window.location.origin, token),

    async open() {
      if (version === null) return;
      await create.mutateAsync({ data: { month, version } });
      await queryClient.invalidateQueries();
    },

    async close(linkId: number) {
      await revoke.mutateAsync({ linkId });
      await queryClient.invalidateQueries();
    },
  };
}

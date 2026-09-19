"use client";

import { useCallback, useEffect, useState } from "react";

import {
  createApiKey,
  listApiKeys,
  revokeApiKey,
  updateApiKey,
} from "@/lib/api/generated/api-keys/api-keys";
import type {
  ApiKeyResponse,
  ApiKeyScope,
  MintedApiKeyResponse,
} from "@/lib/api/generated/model";
import { useCurrentUser } from "@/lib/api/queries";
import { sortKeys } from "@/lib/api-keys";

/**
 * State and actions of the service accounts screen.
 *
 * As everywhere else, coordination lives in a hook so the component carries
 * only the rendering.
 */
export function useApiKeysScreen() {
  const { user: me } = useCurrentUser();
  const [keys, setKeys] = useState<ApiKeyResponse[]>([]);
  const [isLoading, setLoading] = useState(true);
  /**
   * The token of a key just minted.
   *
   * It lives here and nowhere else: never in a query cache, never read back
   * from the server. Closing the panel loses it for good, which is the point.
   */
  const [minted, setMinted] = useState<MintedApiKeyResponse | null>(null);
  /** The key opened beside the list, by id: the row itself comes from `keys`. */
  const [openedId, setOpenedId] = useState<number | null>(null);

  const reload = useCallback(async () => {
    const response = await listApiKeys();
    setKeys(sortKeys(response.data as ApiKeyResponse[]));
    setLoading(false);
  }, []);

  useEffect(() => {
    let alive = true;
    listApiKeys()
      .then((response) => {
        if (!alive) return;
        setKeys(sortKeys(response.data as ApiKeyResponse[]));
        setLoading(false);
      })
      .catch(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, []);

  return {
    keys,
    isLoading,
    isManager: me?.role === "MANAGER",
    minted,
    /** Read from the list rather than held apart: one truth on screen. */
    opened: keys.find((key) => key.id === openedId) ?? null,
    open: setOpenedId,
    close: () => setOpenedId(null),

    /** One reference instant per render, as the teammates screen does. */
    now: new Date(),

    async create(fields: {
      name: string;
      owner_id: number;
      scopes: ApiKeyScope[];
      expires_at: string | null;
    }) {
      const response = await createApiKey({
        ...fields,
        // The form offers a day; the API speaks instants.
        expires_at: fields.expires_at ? `${fields.expires_at}T00:00:00` : null,
      });
      setMinted(response.data as MintedApiKeyResponse);
      await reload();
    },

    /** Closing the panel is what loses the token. Nothing else holds it. */
    dismissMinted: () => setMinted(null),

    async rename(keyId: number, name: string) {
      await updateApiKey(keyId, { name });
      await reload();
    },

    async changeScopes(keyId: number, scopes: ApiKeyScope[]) {
      await updateApiKey(keyId, { scopes });
      await reload();
    },

    async revoke(keyId: number) {
      await revokeApiKey(keyId);
      await reload();
      // Nothing left to correct on a cut key: the panel steps aside.
      setOpenedId(null);
    },
  };
}

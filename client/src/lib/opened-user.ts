"use client";

import { writeUrl, useQueryString } from "@/lib/url-state";

const PARAM = "user";

/**
 * The teammate open in the side panel, held by the URL.
 *
 * Same reasoning as the mission panel: a panel is shared by a link, survives a
 * reload, and going back closes it. Opening therefore pushes a history step,
 * and touches only its own parameter — showing the deactivated accounts must
 * survive a round trip through a panel.
 */
export function useOpenedUser() {
  const params = new URLSearchParams(useQueryString());

  return {
    openedUser: Number(params.get(PARAM)) || null,

    open(userId: number) {
      writeUrl((params) => params.set(PARAM, String(userId)));
    },

    close() {
      writeUrl((params) => params.delete(PARAM));
    },
  };
}

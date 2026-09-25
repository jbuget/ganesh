"use client";

import { writeUrl, useQueryString } from "@/lib/url-state";

const PARAM = "request";

/**
 * The need open in the side panel, held by the URL.
 *
 * Same reasoning as the mission and teammate panels: a panel is shared by a
 * link, survives a reload, and going back closes it. It is also where the
 * bell leads — a notification names the need it speaks of, and opens it.
 */
export function useOpenedRequest() {
  const params = new URLSearchParams(useQueryString());

  return {
    openedRequest: Number(params.get(PARAM)) || null,

    open(requestId: number) {
      writeUrl((params) => params.set(PARAM, String(requestId)));
    },

    close() {
      writeUrl((params) => params.delete(PARAM));
    },
  };
}

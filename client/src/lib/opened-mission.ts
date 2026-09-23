"use client";

import { writeUrl, useQueryString } from "@/lib/url-state";

const PARAM = "mission";
const TAB = "tab";
const AIM = "update";

/**
 * The mission open in the side panel, held by the URL.
 *
 * The URL is the source: a panel is shared by a link, and going back closes it.
 * Opening therefore pushes a history step, and touches only its own
 * parameters: the board filters must survive a round trip through a panel.
 *
 * The tab is part of it: a mission opens on its sheet, but it opens on its
 * thread when the thread is what one went looking for. And inside the thread,
 * one line may be what one came for — a notification names it, and the panel
 * marks it out.
 */
export function useOpenedMission() {
  const query = useQueryString();
  const params = new URLSearchParams(query);
  const value = params.get(PARAM);

  return {
    openedMission: Number(value) || null,
    openTab: params.get(TAB),
    /** The update the visit is about, when one was aimed at. */
    aimedAt: Number(params.get(AIM)) || null,

    open(projectId: number, tab?: string, aimedAt?: number) {
      writeUrl((params) => {
        params.set(PARAM, String(projectId));
        // Without clearing them, the tab and the line of a previous opening
        // would apply to the next mission.
        if (tab) params.set(TAB, tab);
        else params.delete(TAB);
        if (aimedAt) params.set(AIM, String(aimedAt));
        else params.delete(AIM);
      });
    },

    close() {
      writeUrl((params) => {
        params.delete(PARAM);
        params.delete(TAB);
        params.delete(AIM);
      });
    },
  };
}

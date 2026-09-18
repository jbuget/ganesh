"use client";

import { writeUrl, useQueryString } from "@/lib/url-state";

const PARAMETRE = "mission";
const ONGLET = "onglet";

/**
 * The mission open in the side panel, held by the URL.
 *
 * The URL is the source: a panel is shared by a link, and going back closes it.
 * Opening therefore pushes a history step, and touches only its own
 * parameters: the board filters must survive a round trip through a panel.
 *
 * The tab is part of it: a mission opens on its sheet, but it opens on its
 * thread when the thread is what one went looking for.
 */
export function useOpenedMission() {
  const query = useQueryString();
  const params = new URLSearchParams(query);
  const value = params.get(PARAMETRE);

  return {
    openedMission: Number(value) || null,
    ongletOuvert: params.get(ONGLET),

    open(projectId: number, tab?: string) {
      writeUrl((params) => {
        params.set(PARAMETRE, String(projectId));
        // Without clearing it, the tab of a previous opening would apply to
        // the next mission.
        if (tab) params.set(ONGLET, tab);
        else params.delete(ONGLET);
      });
    },

    close() {
      writeUrl((params) => {
        params.delete(PARAMETRE);
        params.delete(ONGLET);
      });
    },
  };
}

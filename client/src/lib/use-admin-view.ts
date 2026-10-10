"use client";

import { useQueryString, writeUrl } from "@/lib/url-state";

/** The two things the administration reads: the platform, and the assistant. */
export type AdminView = "plateforme" | "assistant";

const VIEWS: readonly AdminView[] = ["plateforme", "assistant"];

/**
 * Which tab the administration is on, held by the URL.
 *
 * A conversation opened from the assistant's tab is shared by a link, and the
 * link must land on the tab it was opened from. Replacing the step rather
 * than adding one, as on « Utilisateurs »: going back leaves the screen.
 */
export function useAdminView() {
  const asked = new URLSearchParams(useQueryString()).get("vue");
  const view: AdminView = VIEWS.includes(asked as AdminView)
    ? (asked as AdminView)
    : "plateforme";

  return {
    view,
    show(next: AdminView) {
      writeUrl((params) => {
        // The platform is what a bare address opens on.
        if (next === "plateforme") params.delete("vue");
        else params.set("vue", next);
        return params;
      }, "replace");
    },
  };
}

"use client";

import { useQueryString, writeUrl } from "@/lib/url-state";

/** The two readings the teammates screen offers of one list. */
export type UsersView = "comptes" | "presence";

const VIEWS: readonly UsersView[] = ["comptes", "presence"];

/**
 * Which of the two tabs the teammates screen is on, held by the URL.
 *
 * In the address as the criteria and the order already are: a screen opened on
 * the week is shared by a link — which is what the home screen hands over —
 * and survives a reload. Replacing the step rather than adding one, so going
 * back leaves the screen instead of walking through the tabs one clicked.
 */
export function useUsersView() {
  const query = useQueryString();
  const asked = new URLSearchParams(query).get("vue");
  const view: UsersView = VIEWS.includes(asked as UsersView)
    ? (asked as UsersView)
    : "comptes";

  return {
    view,
    show(next: UsersView) {
      writeUrl((params) => {
        // The accounts tab is the one a bare address opens on: naming it would
        // only put a parameter in every link that says nothing.
        if (next === "comptes") params.delete("vue");
        else params.set("vue", next);
        return params;
      }, "replace");
    },
  };
}

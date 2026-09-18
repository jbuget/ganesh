"use client";

import { useSyncExternalStore } from "react";

/**
 * The URL as the screen's shared state.
 *
 * An open panel, filters set: these are things shared by a link and surviving a
 * reload. They therefore live in the address, not in React state the first F5
 * carries off.
 *
 * `history.pushState` does not fire `popstate`: we notify the subscribers
 * ourselves after every write.
 */
const subscribers = new Set<() => void>();

function query(): string {
  return typeof window === "undefined" ? "" : window.location.search;
}

/** Server-side the address is unknown: no parameters. */
function surLeServeur(): string {
  return "";
}

function subscribe(callback: () => void) {
  subscribers.add(callback);
  window.addEventListener("popstate", callback);

  // The server always renders a bare screen. If the URL says otherwise, nobody
  // would tell React after hydration: we do it on the first subscription.
  if (query()) queueMicrotask(callback);

  return () => {
    subscribers.delete(callback);
    window.removeEventListener("popstate", callback);
  };
}

/** The current parameters, as the address carries them. */
export function useQueryString(): string {
  return useSyncExternalStore(subscribe, query, surLeServeur);
}

/**
 * Reworks the parameters of the address.
 *
 * `push` adds a history step: that is what a navigation calls for, one whose
 * effect going back should undo. `replace` adds none: a filter is set by
 * successive touches, and each must not become a step to walk back through.
 */
export function writeUrl(
  maj: (params: URLSearchParams) => void,
  mode: "pousser" | "remplacer" = "pousser",
): void {
  const params = new URLSearchParams(window.location.search);
  maj(params);

  const queryString = params.toString();
  const address = queryString ? `?${queryString}` : window.location.pathname;
  if (mode === "pousser") window.history.pushState(null, "", address);
  else window.history.replaceState(null, "", address);

  subscribers.forEach((callback) => callback());
}

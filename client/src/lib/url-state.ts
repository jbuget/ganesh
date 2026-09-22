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
function onServer(): string {
  return "";
}

function notify() {
  subscribers.forEach((callback) => callback());
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
  return useSyncExternalStore(subscribe, query, onServer);
}

/**
 * Reworks the parameters of the address.
 *
 * `push` adds a history step: that is what a navigation calls for, one whose
 * effect going back should undo. `replace` adds none: a filter is set by
 * successive touches, and each must not become a step to walk back through.
 */
export function writeUrl(
  update: (params: URLSearchParams) => void,
  mode: "push" | "replace" = "push",
): void {
  const params = new URLSearchParams(window.location.search);
  update(params);

  const queryString = params.toString();
  const address = queryString ? `?${queryString}` : window.location.pathname;
  if (mode === "push") goToAddress(address);
  else {
    window.history.replaceState(null, "", address);
    notify();
  }
}

/**
 * Goes to an address on the screen one is already standing on.
 *
 * Next's router moves without a word to the subscribers here. Crossing to
 * another screen costs nothing: it mounts afresh and reads the address on
 * subscribing. Staying on the same one does not, and a panel asked for from
 * the palette would never open.
 */
export function goToAddress(address: string): void {
  window.history.pushState(null, "", address);
  notify();
}

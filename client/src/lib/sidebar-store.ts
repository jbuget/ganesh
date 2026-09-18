"use client";

import { useSyncExternalStore } from "react";

const CLE = "timesheet.sidebar-repliee";

/**
 * Whether the sidebar is collapsed.
 *
 * It lives outside React and is read with `useSyncExternalStore`: seeding state
 * from `localStorage` on the first render would make server and client
 * diverge, and reading it in an effect would force a `setState` React advises
 * against.
 *
 * No value is cached: `localStorage` is the only source, which lets another tab
 * change it without putting this one out of step.
 */
const subscribers = new Set<() => void>();

function read(): boolean {
  return typeof window !== "undefined" && window.localStorage.getItem(CLE) === "1";
}

function notify() {
  subscribers.forEach((callback) => callback());
}

function subscribe(callback: () => void) {
  subscribers.add(callback);
  window.addEventListener("storage", callback);

  // The server always renders the sidebar expanded. If the preference says
  // otherwise, nobody would tell React after hydration: we do it here, on the
  // first client-side subscription.
  if (read()) queueMicrotask(callback);

  return () => {
    subscribers.delete(callback);
    window.removeEventListener("storage", callback);
  };
}

/** Server-side the sidebar is always expanded: that is the default state. */
function surLeServeur() {
  return false;
}

export function basculerBarreLaterale() {
  window.localStorage.setItem(CLE, read() ? "0" : "1");
  notify();
}

export function useBarreLateraleRepliee(): boolean {
  return useSyncExternalStore(subscribe, read, surLeServeur);
}

"use client";

import { useSyncExternalStore } from "react";

const KEY = "timesheet.mood-reminder-dismissed";

/**
 * The day the reminder was turned down on.
 *
 * A relance one cannot refuse is a relance that harasses, and the moral is
 * given in confidence: turning it down must cost one click and be believed.
 *
 * The day itself is kept rather than a flag. A refusal lasts until the evening
 * and no longer, and a boolean would either have to be cleared by somebody at
 * midnight or go on refusing for ever.
 *
 * Same shape as the fold preference of the sidebar, and for the same reasons:
 * no value is cached, so a second tab that turns the reminder down puts this
 * one straight, and nothing is seeded on the first render, which would make
 * server and client diverge.
 *
 * Per browser, as every preference kept this way is: whoever works from two
 * machines turns it down twice. That is the price of not opening a column for
 * a refusal that expires the same evening.
 */
const subscribers = new Set<() => void>();

function read(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(KEY);
}

function notify() {
  subscribers.forEach((callback) => callback());
}

function subscribe(callback: () => void) {
  subscribers.add(callback);
  window.addEventListener("storage", callback);

  // The server renders as though nothing had been turned down. If something
  // has, nobody would tell React after hydration: we do it here, on the first
  // client-side subscription.
  if (read()) queueMicrotask(callback);

  return () => {
    subscribers.delete(callback);
    window.removeEventListener("storage", callback);
  };
}

/** Server-side nothing has been turned down: that is the default state. */
function onServer() {
  return null;
}

export function dismissMoodReminder(day: string) {
  window.localStorage.setItem(KEY, day);
  notify();
}

export function useMoodReminderDismissedOn(): string | null {
  return useSyncExternalStore(subscribe, read, onServer);
}

"use client";

import { useSyncExternalStore } from "react";

/** Something opened and closed from more than one place, and read by React. */
export interface Toggle {
  open: () => void;
  close: () => void;
  toggle: () => void;
  useIsOpen: () => boolean;
}

/** Server-side nothing is open: it opens on a gesture. */
function onServer(): boolean {
  return false;
}

/**
 * Whether something is open, held outside React.
 *
 * Outside because more than one place opens it — a button, and a shortcut
 * listening to the whole window. Nothing is remembered from one visit to the
 * next: something left open would be a screen nobody asked for.
 */
export function createToggle(): Toggle {
  const subscribers = new Set<() => void>();
  let opened = false;

  function set(value: boolean) {
    if (opened === value) return;
    opened = value;
    subscribers.forEach((callback) => callback());
  }

  function subscribe(callback: () => void) {
    subscribers.add(callback);
    return () => {
      subscribers.delete(callback);
    };
  }

  return {
    open: () => set(true),
    close: () => set(false),
    toggle: () => set(!opened),
    useIsOpen: () => useSyncExternalStore(subscribe, () => opened, onServer),
  };
}

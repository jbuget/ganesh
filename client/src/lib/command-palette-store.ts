"use client";

import { useEffect, useSyncExternalStore } from "react";

/**
 * Whether the palette is open.
 *
 * It lives outside React because two places open it: the field in the sidebar,
 * and the shortcut, which listens to the whole window. Nothing is remembered
 * from one visit to the next — a palette left open would be a screen nobody
 * asked for.
 */
const subscribers = new Set<() => void>();
let opened = false;

function read(): boolean {
  return opened;
}

/** Server-side the palette is always closed: it opens on a gesture. */
function onServer(): boolean {
  return false;
}

function subscribe(callback: () => void) {
  subscribers.add(callback);
  return () => {
    subscribers.delete(callback);
  };
}

function set(value: boolean) {
  if (opened === value) return;
  opened = value;
  subscribers.forEach((callback) => callback());
}

export function openPalette(): void {
  set(true);
}

export function closePalette(): void {
  set(false);
}

export function usePaletteOpen(): boolean {
  return useSyncExternalStore(subscribe, read, onServer);
}

/**
 * ⌘K, or Ctrl+K away from a Mac.
 *
 * It closes what it opens: one reaches for the same keys to put the palette
 * away, and having to aim for Échap to undo a shortcut is a shortcut lost.
 */
export function usePaletteShortcut(): void {
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key !== "k" || !(event.metaKey || event.ctrlKey)) return;
      // The browser has its own use for these keys: the application takes them.
      event.preventDefault();
      set(!opened);
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);
}

/**
 * How the shortcut is written down, for the keyboard one is on.
 *
 * Read through `useSyncExternalStore` rather than in an effect: the server
 * knows nothing of the keyboard, and this is the one way of rendering a first
 * pass it can agree with and correcting it once hydrated.
 */
function shortcut(): string {
  return /Mac|iPhone|iPad/.test(window.navigator.userAgent) ? "⌘K" : "Ctrl K";
}

/** Nothing ever changes it: the keyboard is the one one signed in on. */
function never() {
  return () => {};
}

export function useShortcutHint(): string {
  return useSyncExternalStore(never, shortcut, () => "⌘K");
}

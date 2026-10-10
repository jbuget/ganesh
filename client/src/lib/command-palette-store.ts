"use client";

import { useSyncExternalStore } from "react";

import { createToggle } from "@/lib/toggle-store";
import { useModShortcut } from "@/lib/use-mod-shortcut";

/**
 * Whether the palette is open.
 *
 * Two places open it: the field in the sidebar, and the shortcut, which
 * listens to the whole window.
 */
const palette = createToggle();

export const openPalette = palette.open;
export const closePalette = palette.close;
export const usePaletteOpen = palette.useIsOpen;

/**
 * ⌘K, or Ctrl+K away from a Mac.
 *
 * It closes what it opens: one reaches for the same keys to put the palette
 * away, and having to aim for Échap to undo a shortcut is a shortcut lost.
 */
export function usePaletteShortcut(): void {
  useModShortcut("k", palette.toggle);
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

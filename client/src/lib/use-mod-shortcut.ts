"use client";

import { useEffect } from "react";

/**
 * ⌘ and a key, or Ctrl and the key away from a Mac, anywhere in the window.
 *
 * The browser has its own use for most of these keys: the application takes
 * them, which is the point of offering a shortcut at all.
 */
export function useModShortcut(key: string, onPress: () => void): void {
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key !== key || !(event.metaKey || event.ctrlKey)) return;
      event.preventDefault();
      onPress();
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [key, onPress]);
}

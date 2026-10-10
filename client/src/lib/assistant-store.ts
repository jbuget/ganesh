"use client";

import { createToggle } from "@/lib/toggle-store";
import { useModShortcut } from "@/lib/use-mod-shortcut";

/**
 * Whether the assistant's panel is open.
 *
 * Nothing in the sidebar announces it: for now, it is reached by whoever
 * knows the shortcut, and by nobody else.
 */
const assistant = createToggle();

export const closeAssistant = assistant.close;
export const useAssistantOpen = assistant.useIsOpen;

/**
 * ⌘J, or Ctrl+J away from a Mac — the key the assistants of the tools the team
 * already uses have settled on. It closes what it opens, as ⌘K does.
 */
export function useAssistantShortcut(): void {
  useModShortcut("j", assistant.toggle);
}

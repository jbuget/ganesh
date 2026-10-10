import { describe, expect, it, vi } from "vitest";
import { renderHook } from "@testing-library/react";

import { useModShortcut } from "./use-mod-shortcut";

function press(key: string, modifiers: KeyboardEventInit = {}): KeyboardEvent {
  const event = new KeyboardEvent("keydown", { key, cancelable: true, ...modifiers });
  window.dispatchEvent(event);
  return event;
}

describe("a shortcut held with ⌘, or Ctrl away from a Mac", () => {
  it("answers ⌘ and its key", () => {
    const onPress = vi.fn();
    renderHook(() => useModShortcut("j", onPress));

    press("j", { metaKey: true });

    expect(onPress).toHaveBeenCalledOnce();
  });

  it("answers Ctrl and its key", () => {
    const onPress = vi.fn();
    renderHook(() => useModShortcut("j", onPress));

    press("j", { ctrlKey: true });

    expect(onPress).toHaveBeenCalledOnce();
  });

  it("takes the keys from the browser, which has its own use for them", () => {
    renderHook(() => useModShortcut("j", vi.fn()));

    expect(press("j", { metaKey: true }).defaultPrevented).toBe(true);
  });

  it("ignores the key typed alone", () => {
    const onPress = vi.fn();
    renderHook(() => useModShortcut("j", onPress));

    press("j");

    expect(onPress).not.toHaveBeenCalled();
  });

  it("ignores another key held with ⌘", () => {
    const onPress = vi.fn();
    renderHook(() => useModShortcut("j", onPress));

    press("k", { metaKey: true });

    expect(onPress).not.toHaveBeenCalled();
  });

  it("stops listening once the screen is gone", () => {
    const onPress = vi.fn();
    const { unmount } = renderHook(() => useModShortcut("j", onPress));

    unmount();
    press("j", { metaKey: true });

    expect(onPress).not.toHaveBeenCalled();
  });
});

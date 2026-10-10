import { describe, expect, it } from "vitest";
import { act, renderHook } from "@testing-library/react";

import { createToggle } from "./toggle-store";

describe("a toggle held outside React", () => {
  it("starts closed", () => {
    const toggle = createToggle();

    const { result } = renderHook(() => toggle.useIsOpen());

    expect(result.current).toBe(false);
  });

  it("tells every reader when it opens and closes", () => {
    const toggle = createToggle();
    const { result } = renderHook(() => toggle.useIsOpen());

    act(() => toggle.open());
    expect(result.current).toBe(true);

    act(() => toggle.close());
    expect(result.current).toBe(false);
  });

  it("flips on a toggle, which is what a shortcut does", () => {
    const toggle = createToggle();
    const { result } = renderHook(() => toggle.useIsOpen());

    act(() => toggle.toggle());
    expect(result.current).toBe(true);

    act(() => toggle.toggle());
    expect(result.current).toBe(false);
  });

  it("keeps two toggles apart", () => {
    const palette = createToggle();
    const assistant = createToggle();
    const { result } = renderHook(() => assistant.useIsOpen());

    act(() => palette.open());

    expect(result.current).toBe(false);
  });
});

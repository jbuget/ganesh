import { beforeEach, describe, expect, it } from "vitest";
import { act, renderHook } from "@testing-library/react";

import { toggleSidebar, useSidebarCollapsed } from "./sidebar-store";

describe("fold preference", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("leaves the bar unfolded by default", () => {
    const { result } = renderHook(() => useSidebarCollapsed());

    expect(result.current).toBe(false);
  });

  it("toggles from one call to the next", () => {
    const { result } = renderHook(() => useSidebarCollapsed());
    const origin = result.current;

    act(() => toggleSidebar());

    expect(result.current).toBe(!origin);
  });

  it("keeps the choice in local storage", () => {
    const { result } = renderHook(() => useSidebarCollapsed());
    const expected = !result.current;

    act(() => toggleSidebar());

    expect(window.localStorage.getItem("timesheet.sidebar-collapsed")).toBe(
      expected ? "1" : "0",
    );
  });

  it("applies an already saved preference from the first client render", async () => {
    window.localStorage.setItem("timesheet.sidebar-collapsed", "1");

    const { result } = renderHook(() => useSidebarCollapsed());
    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current).toBe(true);
  });

  it("notifies every subscriber", () => {
    const first = renderHook(() => useSidebarCollapsed());
    const second = renderHook(() => useSidebarCollapsed());

    act(() => toggleSidebar());

    expect(second.result.current).toBe(first.result.current);
  });
});

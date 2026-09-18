import { beforeEach, describe, expect, it } from "vitest";
import { act, renderHook } from "@testing-library/react";

import { toggleSidebar, useBarreLateraleRepliee } from "./sidebar-store";

describe("fold preference", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("leaves the bar unfolded by default", () => {
    const { result } = renderHook(() => useBarreLateraleRepliee());

    expect(result.current).toBe(false);
  });

  it("toggles from one call to the next", () => {
    const { result } = renderHook(() => useBarreLateraleRepliee());
    const origin = result.current;

    act(() => toggleSidebar());

    expect(result.current).toBe(!origin);
  });

  it("keeps the choice in local storage", () => {
    const { result } = renderHook(() => useBarreLateraleRepliee());
    const expected = !result.current;

    act(() => toggleSidebar());

    expect(window.localStorage.getItem("timesheet.sidebar-repliee")).toBe(
      expected ? "1" : "0",
    );
  });

  it("applies an already saved preference from the first client render", async () => {
    window.localStorage.setItem("timesheet.sidebar-repliee", "1");

    const { result } = renderHook(() => useBarreLateraleRepliee());
    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current).toBe(true);
  });

  it("notifies every subscriber", () => {
    const first = renderHook(() => useBarreLateraleRepliee());
    const second = renderHook(() => useBarreLateraleRepliee());

    act(() => toggleSidebar());

    expect(second.result.current).toBe(first.result.current);
  });
});

import { beforeEach, describe, expect, it } from "vitest";
import { act, renderHook } from "@testing-library/react";

import { basculerBarreLaterale, useBarreLateraleRepliee } from "./sidebar-store";

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
    const depart = result.current;

    act(() => basculerBarreLaterale());

    expect(result.current).toBe(!depart);
  });

  it("keeps the choice in local storage", () => {
    const { result } = renderHook(() => useBarreLateraleRepliee());
    const attendu = !result.current;

    act(() => basculerBarreLaterale());

    expect(window.localStorage.getItem("timesheet.sidebar-repliee")).toBe(
      attendu ? "1" : "0",
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
    const premier = renderHook(() => useBarreLateraleRepliee());
    const second = renderHook(() => useBarreLateraleRepliee());

    act(() => basculerBarreLaterale());

    expect(second.result.current).toBe(premier.result.current);
  });
});

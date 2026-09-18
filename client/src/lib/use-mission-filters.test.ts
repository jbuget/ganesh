import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { useMissionFilters } from "./use-mission-filters";
import { useOpenedMission } from "./opened-mission";

beforeEach(() => {
  window.history.replaceState(null, "", "/kanban");
});

describe("useMissionFilters", () => {
  it("starts from an unfiltered board", () => {
    const { result } = renderHook(() => useMissionFilters());

    expect(result.current.hasFilter).toBe(false);
  });

  it("reads back from the URL the criterion just set", () => {
    const { result } = renderHook(() => useMissionFilters());

    act(() => result.current.set({ phases: ["development"] }));

    expect(result.current.filters.phases).toEqual(["development"]);
    expect(window.location.search).toContain("phase=development");
  });

  it("keeps the other criteria when changing one of them", () => {
    const { result } = renderHook(() => useMissionFilters());

    act(() => result.current.set({ phases: ["scoping"] }));
    act(() => result.current.set({ name: "portail" }));

    expect(result.current.filters).toMatchObject({
      phases: ["scoping"],
      name: "portail",
    });
  });

  it("adds no history step: setting a filter is not navigating", () => {
    const profondeur = window.history.length;
    const { result } = renderHook(() => useMissionFilters());

    act(() => result.current.set({ name: "por" }));
    act(() => result.current.set({ name: "port" }));

    expect(window.history.length).toBe(profondeur);
  });

  it("returns the whole board once cleared", () => {
    const { result } = renderHook(() => useMissionFilters());

    act(() => result.current.set({ phases: ["scoping"], name: "portail" }));
    act(() => result.current.clear());

    expect(result.current.hasFilter).toBe(false);
    expect(window.location.search).toBe("");
  });
});

describe("living alongside the mission panel", () => {
  it("opening a mission does not lose the filters set", () => {
    const { result: filters } = renderHook(() => useMissionFilters());
    const { result: panel } = renderHook(() => useOpenedMission());

    act(() => filters.current.set({ phases: ["scoping"] }));
    act(() => panel.current.open(12));

    expect(panel.current.openedMission).toBe(12);
    expect(filters.current.filters.phases).toEqual(["scoping"]);
  });

  it("closing the panel leaves the filters in place", () => {
    const { result: filters } = renderHook(() => useMissionFilters());
    const { result: panel } = renderHook(() => useOpenedMission());

    act(() => filters.current.set({ name: "portail" }));
    act(() => panel.current.open(12));
    act(() => panel.current.close());

    expect(panel.current.openedMission).toBeNull();
    expect(filters.current.filters.name).toBe("portail");
  });
});

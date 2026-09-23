import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { useOpenedMission } from "./opened-mission";

beforeEach(() => {
  window.history.replaceState(null, "", "/projects");
});

describe("useOpenedMission", () => {
  it("starts from a screen with no panel", () => {
    const { result } = renderHook(() => useOpenedMission());

    expect(result.current.openedMission).toBeNull();
    expect(result.current.openTab).toBeNull();
  });

  it("opens a mission on its panel", () => {
    const { result } = renderHook(() => useOpenedMission());

    act(() => result.current.open(29));

    expect(result.current.openedMission).toBe(29);
    expect(result.current.openTab).toBeNull();
  });

  it("opens a mission straight onto a tab", () => {
    const { result } = renderHook(() => useOpenedMission());

    act(() => result.current.open(29, "updates"));

    expect(result.current.openedMission).toBe(29);
    expect(result.current.openTab).toBe("updates");
  });

  it("forgets the tab of a previous opening", () => {
    const { result } = renderHook(() => useOpenedMission());

    act(() => result.current.open(29, "updates"));
    act(() => result.current.open(30));

    expect(result.current.openTab).toBeNull();
  });

  it("aims at one update inside the thread", () => {
    const { result } = renderHook(() => useOpenedMission());

    act(() => result.current.open(29, "updates", 412));

    expect(result.current.openTab).toBe("updates");
    expect(result.current.aimedAt).toBe(412);
  });

  it("forgets the update a previous opening aimed at", () => {
    const { result } = renderHook(() => useOpenedMission());

    act(() => result.current.open(29, "updates", 412));
    act(() => result.current.open(30, "updates"));

    expect(result.current.aimedAt).toBeNull();
  });

  it("closes the panel without leaving its tab behind", () => {
    const { result } = renderHook(() => useOpenedMission());

    act(() => result.current.open(29, "updates", 412));
    act(() => result.current.close());

    expect(result.current.openedMission).toBeNull();
    expect(window.location.search).not.toContain("tab");
    expect(window.location.search).not.toContain("update");
  });

  it("leaves the screen's other parameters untouched", () => {
    window.history.replaceState(null, "", "/kanban?phase=development");
    const { result } = renderHook(() => useOpenedMission());

    act(() => result.current.open(29, "updates"));
    act(() => result.current.close());

    expect(window.location.search).toContain("phase=development");
  });
});

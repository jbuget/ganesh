import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { useMissionFilters } from "./use-mission-filters";
import { useOpenedMission } from "./mission-ouverte";

beforeEach(() => {
  window.history.replaceState(null, "", "/kanban");
});

describe("useMissionFilters", () => {
  it("part d'un tableau sans filtre", () => {
    const { result } = renderHook(() => useMissionFilters());

    expect(result.current.hasFilter).toBe(false);
  });

  it("relit dans l'URL le critère qu'on vient de poser", () => {
    const { result } = renderHook(() => useMissionFilters());

    act(() => result.current.set({ phases: ["build"] }));

    expect(result.current.filters.phases).toEqual(["build"]);
    expect(window.location.search).toContain("phase=build");
  });

  it("garde les autres critères en changeant l'un d'eux", () => {
    const { result } = renderHook(() => useMissionFilters());

    act(() => result.current.set({ phases: ["scoping"] }));
    act(() => result.current.set({ name: "portail" }));

    expect(result.current.filters).toMatchObject({
      phases: ["scoping"],
      name: "portail",
    });
  });

  it("n'ajoute aucune étape d'historique : régler un filtre n'est pas naviguer", () => {
    const profondeur = window.history.length;
    const { result } = renderHook(() => useMissionFilters());

    act(() => result.current.set({ name: "por" }));
    act(() => result.current.set({ name: "port" }));

    expect(window.history.length).toBe(profondeur);
  });

  it("rend le tableau entier une fois effacé", () => {
    const { result } = renderHook(() => useMissionFilters());

    act(() => result.current.set({ phases: ["scoping"], name: "portail" }));
    act(() => result.current.clear());

    expect(result.current.hasFilter).toBe(false);
    expect(window.location.search).toBe("");
  });
});

describe("cohabitation avec le panneau mission", () => {
  it("ouvrir une mission ne perd pas les filtres posés", () => {
    const { result: filters } = renderHook(() => useMissionFilters());
    const { result: panel } = renderHook(() => useOpenedMission());

    act(() => filters.current.set({ phases: ["scoping"] }));
    act(() => panel.current.open(12));

    expect(panel.current.openedMission).toBe(12);
    expect(filters.current.filters.phases).toEqual(["scoping"]);
  });

  it("refermer le panneau laisse les filtres en place", () => {
    const { result: filters } = renderHook(() => useMissionFilters());
    const { result: panel } = renderHook(() => useOpenedMission());

    act(() => filters.current.set({ name: "portail" }));
    act(() => panel.current.open(12));
    act(() => panel.current.close());

    expect(panel.current.openedMission).toBeNull();
    expect(filters.current.filters.name).toBe("portail");
  });
});

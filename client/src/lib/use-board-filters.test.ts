import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { useBoardFilters } from "./use-board-filters";
import { useMissionOuverte } from "./mission-ouverte";

beforeEach(() => {
  window.history.replaceState(null, "", "/kanban");
});

describe("useBoardFilters", () => {
  it("part d'un tableau sans filtre", () => {
    const { result } = renderHook(() => useBoardFilters());

    expect(result.current.actif).toBe(false);
  });

  it("relit dans l'URL le critère qu'on vient de poser", () => {
    const { result } = renderHook(() => useBoardFilters());

    act(() => result.current.definir({ phases: ["realisation"] }));

    expect(result.current.filtres.phases).toEqual(["realisation"]);
    expect(window.location.search).toContain("phase=realisation");
  });

  it("garde les autres critères en changeant l'un d'eux", () => {
    const { result } = renderHook(() => useBoardFilters());

    act(() => result.current.definir({ phases: ["cadrage"] }));
    act(() => result.current.definir({ nom: "portail" }));

    expect(result.current.filtres).toMatchObject({
      phases: ["cadrage"],
      nom: "portail",
    });
  });

  it("n'ajoute aucune étape d'historique : régler un filtre n'est pas naviguer", () => {
    const profondeur = window.history.length;
    const { result } = renderHook(() => useBoardFilters());

    act(() => result.current.definir({ nom: "por" }));
    act(() => result.current.definir({ nom: "port" }));

    expect(window.history.length).toBe(profondeur);
  });

  it("rend le tableau entier une fois effacé", () => {
    const { result } = renderHook(() => useBoardFilters());

    act(() => result.current.definir({ phases: ["cadrage"], nom: "portail" }));
    act(() => result.current.effacer());

    expect(result.current.actif).toBe(false);
    expect(window.location.search).toBe("");
  });
});

describe("cohabitation avec le panneau mission", () => {
  it("ouvrir une mission ne perd pas les filtres posés", () => {
    const { result: filtres } = renderHook(() => useBoardFilters());
    const { result: panneau } = renderHook(() => useMissionOuverte());

    act(() => filtres.current.definir({ phases: ["cadrage"] }));
    act(() => panneau.current.ouvrir(12));

    expect(panneau.current.missionOuverte).toBe(12);
    expect(filtres.current.filtres.phases).toEqual(["cadrage"]);
  });

  it("refermer le panneau laisse les filtres en place", () => {
    const { result: filtres } = renderHook(() => useBoardFilters());
    const { result: panneau } = renderHook(() => useMissionOuverte());

    act(() => filtres.current.definir({ nom: "portail" }));
    act(() => panneau.current.ouvrir(12));
    act(() => panneau.current.fermer());

    expect(panneau.current.missionOuverte).toBeNull();
    expect(filtres.current.filtres.nom).toBe("portail");
  });
});

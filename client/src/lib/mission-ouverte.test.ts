import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { useMissionOuverte } from "./mission-ouverte";

beforeEach(() => {
  window.history.replaceState(null, "", "/projets");
});

describe("useMissionOuverte", () => {
  it("part d'un écran sans panneau", () => {
    const { result } = renderHook(() => useMissionOuverte());

    expect(result.current.missionOuverte).toBeNull();
    expect(result.current.ongletOuvert).toBeNull();
  });

  it("ouvre une mission sur son panneau", () => {
    const { result } = renderHook(() => useMissionOuverte());

    act(() => result.current.ouvrir(29));

    expect(result.current.missionOuverte).toBe(29);
    expect(result.current.ongletOuvert).toBeNull();
  });

  it("ouvre une mission directement sur un onglet", () => {
    const { result } = renderHook(() => useMissionOuverte());

    act(() => result.current.ouvrir(29, "updates"));

    expect(result.current.missionOuverte).toBe(29);
    expect(result.current.ongletOuvert).toBe("updates");
  });

  it("oublie l'onglet d'une ouverture précédente", () => {
    const { result } = renderHook(() => useMissionOuverte());

    act(() => result.current.ouvrir(29, "updates"));
    act(() => result.current.ouvrir(30));

    expect(result.current.ongletOuvert).toBeNull();
  });

  it("referme le panneau sans laisser son onglet derrière lui", () => {
    const { result } = renderHook(() => useMissionOuverte());

    act(() => result.current.ouvrir(29, "updates"));
    act(() => result.current.fermer());

    expect(result.current.missionOuverte).toBeNull();
    expect(window.location.search).not.toContain("onglet");
  });

  it("laisse intacts les autres paramètres de l'écran", () => {
    window.history.replaceState(null, "", "/kanban?phase=realisation");
    const { result } = renderHook(() => useMissionOuverte());

    act(() => result.current.ouvrir(29, "updates"));
    act(() => result.current.fermer());

    expect(window.location.search).toContain("phase=realisation");
  });
});

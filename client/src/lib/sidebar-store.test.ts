import { beforeEach, describe, expect, it } from "vitest";
import { act, renderHook } from "@testing-library/react";

import { basculerBarreLaterale, useBarreLateraleRepliee } from "./sidebar-store";

describe("préférence de repli", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("laisse la barre dépliée par défaut", () => {
    const { result } = renderHook(() => useBarreLateraleRepliee());

    expect(result.current).toBe(false);
  });

  it("bascule d'un appel à l'autre", () => {
    const { result } = renderHook(() => useBarreLateraleRepliee());
    const depart = result.current;

    act(() => basculerBarreLaterale());

    expect(result.current).toBe(!depart);
  });

  it("retient le choix dans le stockage local", () => {
    const { result } = renderHook(() => useBarreLateraleRepliee());
    const attendu = !result.current;

    act(() => basculerBarreLaterale());

    expect(window.localStorage.getItem("timesheet.sidebar-repliee")).toBe(
      attendu ? "1" : "0",
    );
  });

  it("applique une préférence déjà enregistrée dès le premier rendu client", async () => {
    window.localStorage.setItem("timesheet.sidebar-repliee", "1");

    const { result } = renderHook(() => useBarreLateraleRepliee());
    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current).toBe(true);
  });

  it("prévient tous les abonnés", () => {
    const premier = renderHook(() => useBarreLateraleRepliee());
    const second = renderHook(() => useBarreLateraleRepliee());

    act(() => basculerBarreLaterale());

    expect(second.result.current).toBe(premier.result.current);
  });
});

import { describe, expect, it } from "vitest";
import { renderHook } from "@testing-library/react";

import { useLastNonNull } from "./use-last-non-null";

describe("useLastNonNull", () => {
  it("renvoie la valeur courante quand elle existe", () => {
    const { result } = renderHook(() => useLastNonNull("Portail"));

    expect(result.current).toBe("Portail");
  });

  it("retient la dernière valeur quand elle repasse à null", () => {
    const { result, rerender } = renderHook(({ valeur }) => useLastNonNull(valeur), {
      initialProps: { valeur: "Portail" as string | null },
    });

    rerender({ valeur: null });

    expect(result.current).toBe("Portail");
  });

  it("suit les changements successifs", () => {
    const { result, rerender } = renderHook(({ valeur }) => useLastNonNull(valeur), {
      initialProps: { valeur: "Portail" as string | null },
    });

    rerender({ valeur: "Extranet" });
    rerender({ valeur: null });

    expect(result.current).toBe("Extranet");
  });

  it("renvoie null tant qu'aucune valeur n'a été reçue", () => {
    const { result } = renderHook(() => useLastNonNull<string>(null));

    expect(result.current).toBeNull();
  });
});

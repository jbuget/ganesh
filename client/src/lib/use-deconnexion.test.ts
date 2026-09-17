import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderHook } from "@testing-library/react";

import { useDeconnexion } from "./use-deconnexion";

const router = vi.hoisted(() => ({ replace: vi.fn(), refresh: vi.fn() }));
const queryClient = vi.hoisted(() => ({ clear: vi.fn() }));

vi.mock("next/navigation", () => ({ useRouter: () => router }));
vi.mock("@tanstack/react-query", () => ({ useQueryClient: () => queryClient }));

describe("useDeconnexion", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 204 })),
    );
  });

  it("demande au serveur d'effacer la session", async () => {
    const { result } = renderHook(() => useDeconnexion());

    await result.current();

    expect(fetch).toHaveBeenCalledWith("/api/auth/signout", { method: "POST" });
  });

  it("vide le cache avant de renvoyer à l'accueil", async () => {
    const { result } = renderHook(() => useDeconnexion());

    await result.current();

    // Sans cela, l'ecran suivant reafficherait les donnees de la personne qui
    // vient de partir, le temps d'un rechargement.
    expect(queryClient.clear).toHaveBeenCalled();
    expect(router.replace).toHaveBeenCalledWith("/");
    expect(router.refresh).toHaveBeenCalled();
  });
});

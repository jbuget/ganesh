import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, renderHook, waitFor } from "@testing-library/react";

import { useProjectUpdates } from "./use-project-updates";

const api = vi.hoisted(() => ({
  listProjectUpdates: vi.fn(),
  postProjectUpdate: vi.fn(),
  editProjectUpdate: vi.fn(),
  removeProjectUpdate: vi.fn(),
}));

vi.mock("@/lib/api/generated/projects/projects", () => api);

beforeEach(() => {
  vi.clearAllMocks();
  api.listProjectUpdates.mockResolvedValue({ data: [] });
  api.postProjectUpdate.mockResolvedValue({ data: {} });
  api.editProjectUpdate.mockResolvedValue({ data: {} });
  api.removeProjectUpdate.mockResolvedValue({ data: {} });
});

async function fil(onEcriture?: () => void | Promise<void>) {
  const { result } = renderHook(() => useProjectUpdates(7, onEcriture));
  await waitFor(() => expect(result.current.fil).not.toBeNull());
  return result;
}

describe("useProjectUpdates", () => {
  it("prévient l'écran d'où l'on vient quand une mise à jour est publiée", async () => {
    const prevenir = vi.fn();
    const result = await fil(prevenir);

    await act(async () => {
      await result.current.publier("Cadrage lancé");
    });

    expect(api.postProjectUpdate).toHaveBeenCalledWith(7, { texte: "Cadrage lancé" });
    expect(prevenir).toHaveBeenCalledTimes(1);
  });

  it("le prévient aussi d'une correction", async () => {
    const prevenir = vi.fn();
    const result = await fil(prevenir);

    await act(async () => {
      await result.current.corriger(3, "Cadrage relancé");
    });

    expect(prevenir).toHaveBeenCalledTimes(1);
  });

  it("le prévient d'un retrait, qui change aussi ce que la liste annonce", async () => {
    const prevenir = vi.fn();
    const result = await fil(prevenir);

    await act(async () => {
      await result.current.retirer(3);
    });

    expect(prevenir).toHaveBeenCalledTimes(1);
  });

  it("s'en passe quand personne n'écoute", async () => {
    const result = await fil();

    await act(async () => {
      await result.current.publier("Seul au monde");
    });

    expect(api.postProjectUpdate).toHaveBeenCalledOnce();
  });

  it("ne prévient personne à la simple lecture du fil", async () => {
    const prevenir = vi.fn();
    await fil(prevenir);

    expect(prevenir).not.toHaveBeenCalled();
  });
});

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
    const notify = vi.fn();
    const result = await fil(notify);

    await act(async () => {
      await result.current.publier("Cadrage lancé");
    });

    expect(api.postProjectUpdate).toHaveBeenCalledWith(7, { body: "Cadrage lancé" });
    expect(notify).toHaveBeenCalledTimes(1);
  });

  it("le prévient aussi d'une correction", async () => {
    const notify = vi.fn();
    const result = await fil(notify);

    await act(async () => {
      await result.current.corriger(3, "Cadrage relancé");
    });

    expect(notify).toHaveBeenCalledTimes(1);
  });

  it("le prévient d'un retrait, qui change aussi ce que la liste annonce", async () => {
    const notify = vi.fn();
    const result = await fil(notify);

    await act(async () => {
      await result.current.retirer(3);
    });

    expect(notify).toHaveBeenCalledTimes(1);
  });

  it("s'en passe quand personne n'écoute", async () => {
    const result = await fil();

    await act(async () => {
      await result.current.publier("Seul au monde");
    });

    expect(api.postProjectUpdate).toHaveBeenCalledOnce();
  });

  it("ne prévient personne à la simple lecture du fil", async () => {
    const notify = vi.fn();
    await fil(notify);

    expect(notify).not.toHaveBeenCalled();
  });
});

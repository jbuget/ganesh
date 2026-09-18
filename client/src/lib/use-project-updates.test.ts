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

async function thread(onWrite?: () => void | Promise<void>) {
  const { result } = renderHook(() => useProjectUpdates(7, onWrite));
  await waitFor(() => expect(result.current.thread).not.toBeNull());
  return result;
}

describe("useProjectUpdates", () => {
  it("tells the screen one came from when an update is posted", async () => {
    const notify = vi.fn();
    const result = await thread(notify);

    await act(async () => {
      await result.current.publish("Cadrage lancé");
    });

    expect(api.postProjectUpdate).toHaveBeenCalledWith(7, { body: "Cadrage lancé" });
    expect(notify).toHaveBeenCalledTimes(1);
  });

  it("tells it about a correction too", async () => {
    const notify = vi.fn();
    const result = await thread(notify);

    await act(async () => {
      await result.current.edit(3, "Cadrage relancé");
    });

    expect(notify).toHaveBeenCalledTimes(1);
  });

  it("tells it about a withdrawal, which also changes what the list announces", async () => {
    const notify = vi.fn();
    const result = await thread(notify);

    await act(async () => {
      await result.current.remove(3);
    });

    expect(notify).toHaveBeenCalledTimes(1);
  });

  it("does without when nobody is listening", async () => {
    const result = await thread();

    await act(async () => {
      await result.current.publish("Seul au monde");
    });

    expect(api.postProjectUpdate).toHaveBeenCalledOnce();
  });

  it("tells nobody when the thread is merely read", async () => {
    const notify = vi.fn();
    await thread(notify);

    expect(notify).not.toHaveBeenCalled();
  });
});

import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, renderHook } from "@testing-library/react";

import { useTagManagement } from "./use-tag-management";

const api = vi.hoisted(() => ({
  renameTag: vi.fn(),
  recolorTag: vi.fn(),
  mergeTags: vi.fn(),
}));
const cache = vi.hoisted(() => ({ invalidateQueries: vi.fn() }));

vi.mock("@/lib/api/generated/tags/tags", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api/generated/tags/tags")>()),
  ...api,
}));
vi.mock("@tanstack/react-query", () => ({ useQueryClient: () => cache }));

beforeEach(() => {
  vi.clearAllMocks();
  for (const call of Object.values(api)) call.mockResolvedValue({ data: {} });
  cache.invalidateQueries.mockResolvedValue(undefined);
});

describe("useTagManagement", () => {
  it("renames a tag by its id", async () => {
    const { result } = renderHook(() => useTagManagement());

    await act(() => result.current.rename(4, "Suez Group"));

    expect(api.renameTag).toHaveBeenCalledWith(4, { name: "Suez Group" });
  });

  it("gives a tag another colour of the palette", async () => {
    const { result } = renderHook(() => useTagManagement());

    await act(() => result.current.recolor(4, "violet"));

    expect(api.recolorTag).toHaveBeenCalledWith(4, { color: "violet" });
  });

  it("folds a tag into another one", async () => {
    const { result } = renderHook(() => useTagManagement());

    await act(() => result.current.merge(4, 9));

    expect(api.mergeTags).toHaveBeenCalledWith(4, { target_id: 9 });
  });

  /**
   * A tag changed moves every mission carrying it: the reference list and the
   * board behind the dialog read them, and must not go on showing the old name.
   */
  it.each([
    ["a renaming", (h: ReturnType<typeof useTagManagement>) => h.rename(1, "X")],
    ["a recolouring", (h: ReturnType<typeof useTagManagement>) => h.recolor(1, "red")],
    ["a merge", (h: ReturnType<typeof useTagManagement>) => h.merge(1, 2)],
  ])("makes every screen read again after %s", async (_what, change) => {
    const { result } = renderHook(() => useTagManagement());

    await act(() => change(result.current));

    expect(cache.invalidateQueries).toHaveBeenCalledWith();
  });

  it("lets a refusal through, for the row to say why", async () => {
    api.renameTag.mockRejectedValue(new Error("409"));
    const { result } = renderHook(() => useTagManagement());

    await expect(result.current.rename(4, "Suez")).rejects.toThrow("409");
    expect(cache.invalidateQueries).not.toHaveBeenCalled();
  });
});

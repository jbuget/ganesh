import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, renderHook } from "@testing-library/react";

import { useMood } from "./use-mood";

const moods = vi.hoisted(() => ({
  setMood: vi.fn(),
  clearMood: vi.fn(),
  getGetMyMoodsQueryKey: () => ["moods", "me"],
}));
const queries = vi.hoisted(() => ({
  days: [] as { day: string; level: string | null }[],
  useMyMoods: () => ({ days: queries.days, isLoading: false }),
}));

vi.mock("@/lib/api/generated/moods/moods", () => moods);
vi.mock("@/lib/api/queries", () => queries);
vi.mock("@tanstack/react-query", () => ({
  useQueryClient: () => ({ invalidateQueries: vi.fn() }),
}));

beforeEach(() => {
  vi.clearAllMocks();
  queries.days = [{ day: "2026-09-18", level: null }];
});

describe("useMood", () => {
  it("posts a day one has not answered for", async () => {
    const { result } = renderHook(() => useMood());

    await act(() => result.current.post("2026-09-18", "good"));

    expect(moods.setMood).toHaveBeenCalledWith({ day: "2026-09-18", level: "good" });
    expect(moods.clearMood).not.toHaveBeenCalled();
  });

  it("changes the answer when another face is picked", async () => {
    queries.days = [{ day: "2026-09-18", level: "good" }];
    const { result } = renderHook(() => useMood());

    await act(() => result.current.post("2026-09-18", "bad"));

    expect(moods.setMood).toHaveBeenCalledWith({ day: "2026-09-18", level: "bad" });
    expect(moods.clearMood).not.toHaveBeenCalled();
  });

  it("takes the answer back when the face already chosen is picked again", async () => {
    // The way out is the way in: five small faces are easily mis-clicked, and
    // the whole team reads the result under one's name.
    queries.days = [{ day: "2026-09-18", level: "good" }];
    const { result } = renderHook(() => useMood());

    await act(() => result.current.post("2026-09-18", "good"));

    expect(moods.clearMood).toHaveBeenCalledWith("2026-09-18");
    expect(moods.setMood).not.toHaveBeenCalled();
  });

  it("answers for the day it was given, not for the other open one", async () => {
    queries.days = [
      { day: "2026-09-18", level: "good" },
      { day: "2026-09-17", level: null },
    ];
    const { result } = renderHook(() => useMood());

    await act(() => result.current.post("2026-09-17", "good"));

    expect(moods.setMood).toHaveBeenCalledWith({ day: "2026-09-17", level: "good" });
    expect(moods.clearMood).not.toHaveBeenCalled();
  });
});

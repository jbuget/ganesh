import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, renderHook } from "@testing-library/react";

import { useMood } from "./use-mood";

const moods = vi.hoisted(() => ({
  setMood: vi.fn(),
  clearMood: vi.fn(),
  getGetMyMoodsQueryKey: () => ["/api/v1/moods/me"],
  getGetTeamMoodsQueryKey: () => ["/api/v1/moods/team"],
}));
const client = vi.hoisted(() => ({ invalidateQueries: vi.fn() }));
const queries = vi.hoisted(() => ({
  days: [] as { day: string; level: string | null }[],
  useMyMoods: () => ({ days: queries.days, isLoading: false }),
}));

// The reading of « may this person write? » is its own hook, and its own
// tests: here it is answered yes, so that what is under test stays what the
// file says it is.
const mayWrite = vi.hoisted(() => ({ value: true }));
vi.mock("@/lib/use-may-write", () => ({ useMayWrite: () => mayWrite.value }));

vi.mock("@/lib/api/generated/moods/moods", () => moods);
vi.mock("@/lib/api/queries", () => queries);
vi.mock("@tanstack/react-query", () => ({
  useQueryClient: () => client,
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

  it("replays the team's fortnight too, not just one's own days", async () => {
    // Queries stay fresh for half a minute: without this, walking over to the
    // team screen right after answering showed the mood one had just changed.
    const { result } = renderHook(() => useMood());

    await act(() => result.current.post("2026-09-18", "good"));

    expect(client.invalidateQueries.mock.calls.map(([call]) => call.queryKey)).toEqual([
      ["/api/v1/moods/me"],
      ["/api/v1/moods/team"],
    ]);
  });

  it("replays both after taking an answer back as well", async () => {
    queries.days = [{ day: "2026-09-18", level: "good" }];
    const { result } = renderHook(() => useMood());

    await act(() => result.current.post("2026-09-18", "good"));

    expect(client.invalidateQueries).toHaveBeenCalledTimes(2);
  });
});

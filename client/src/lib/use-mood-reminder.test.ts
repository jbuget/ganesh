import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, renderHook } from "@testing-library/react";

import { useMoodReminder } from "./use-mood-reminder";

const TODAY = "2026-09-23";
const BEFORE = "2026-09-22";

const mood = vi.hoisted(() => ({
  isLoading: false,
  today: "2026-09-23",
  days: [] as { day: string; level: string | null }[],
  savingDay: null as string | null,
  post: vi.fn(),
}));
const pathname = vi.hoisted(() => ({ value: "/timesheet" }));

vi.mock("@/lib/use-mood", () => ({ useMood: () => mood }));
vi.mock("next/navigation", () => ({ usePathname: () => pathname.value }));

/** Only the clock: the store leans on `queueMicrotask`, which must stay real. */
function at(hour: number, minute = 0) {
  const clock = `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
  vi.setSystemTime(new Date(`${TODAY}T${clock}:00`));
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date", "setInterval", "clearInterval"] });
  window.localStorage.clear();
  vi.clearAllMocks();
  mood.days = [
    { day: TODAY, level: null },
    { day: BEFORE, level: "good" },
  ];
  mood.savingDay = null;
  pathname.value = "/timesheet";
  at(17);
});

afterEach(() => {
  vi.useRealTimers();
});

describe("when the reminder asks", () => {
  it("asks once the afternoon is over and the day is unanswered", () => {
    const { result } = renderHook(() => useMoodReminder());

    expect(result.current.show).toBe(true);
  });

  it("says nothing before four o'clock", () => {
    // A mood posted at half past nine measures the commute, not the day.
    at(9);

    const { result } = renderHook(() => useMoodReminder());

    expect(result.current.show).toBe(false);
  });

  it("says nothing once the day has been answered for", () => {
    mood.days = [{ day: TODAY, level: "hard" }];

    const { result } = renderHook(() => useMoodReminder());

    expect(result.current.show).toBe(false);
  });

  it("says nothing on a day one may not answer for", () => {
    // A Saturday carries no today: the domain decides that, not this hook.
    mood.days = [{ day: BEFORE, level: null }];

    const { result } = renderHook(() => useMoodReminder());

    expect(result.current.show).toBe(false);
  });

  it("reaches four o'clock on a tab left open since the morning", () => {
    at(15, 59);
    const { result } = renderHook(() => useMoodReminder());
    expect(result.current.show).toBe(false);

    act(() => {
      at(16, 0);
      vi.advanceTimersByTime(60_000);
    });

    expect(result.current.show).toBe(true);
  });
});

describe("where the reminder keeps quiet", () => {
  it("never asks on the team screen", () => {
    // Answering there is answering under the eyes of what the answer is about.
    pathname.value = "/mood";

    const { result } = renderHook(() => useMoodReminder());

    expect(result.current.show).toBe(false);
  });

  it("never asks on the home screen, which already carries the check-in", () => {
    pathname.value = "/";

    const { result } = renderHook(() => useMoodReminder());

    expect(result.current.show).toBe(false);
  });
});

describe("turning it down", () => {
  it("is believed for the rest of the day", () => {
    const { result } = renderHook(() => useMoodReminder());

    act(() => result.current.dismiss());

    expect(result.current.show).toBe(false);
  });

  it("asks again the next day", () => {
    window.localStorage.setItem("timesheet.mood-reminder-dismissed", BEFORE);

    const { result } = renderHook(() => useMoodReminder());

    expect(result.current.show).toBe(true);
  });
});

describe("answering from the reminder", () => {
  it("posts for today, and for no other day", () => {
    const { result } = renderHook(() => useMoodReminder());

    result.current.post("excellent");

    expect(mood.post).toHaveBeenCalledWith(TODAY, "excellent");
  });

  it("holds the faces while today's answer travels", () => {
    mood.savingDay = TODAY;

    const { result } = renderHook(() => useMoodReminder());

    expect(result.current.saving).toBe(true);
  });
});

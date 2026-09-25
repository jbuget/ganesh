import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, renderHook } from "@testing-library/react";

import { REMINDER_DELAY_MS, useMoodReminder } from "./use-mood-reminder";

const TODAY = "2026-09-23";
const BEFORE = "2026-09-22";

const mood = vi.hoisted(() => ({
  isLoading: false,
  today: "2026-09-23",
  days: [] as { day: string; level: string | null }[],
  savingDay: null as string | null,
  mayAnswer: true,
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

function wait(ms: number) {
  act(() => {
    vi.advanceTimersByTime(ms);
  });
}

/**
 * Rendered, then left alone long enough to be asked.
 *
 * Every case waits, the ones that expect nothing included: a `show` left false
 * by the delay alone would say nothing about the rule under test.
 */
function ask() {
  const rendered = renderHook(() => useMoodReminder());
  wait(REMINDER_DELAY_MS);
  return rendered;
}

beforeEach(() => {
  vi.useFakeTimers({
    toFake: ["Date", "setInterval", "clearInterval", "setTimeout", "clearTimeout"],
  });
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
    const { result } = ask();

    expect(result.current.show).toBe(true);
  });

  it("says nothing before four o'clock", () => {
    // A mood posted at half past nine measures the commute, not the day.
    at(9);

    const { result } = ask();

    expect(result.current.show).toBe(false);
  });

  it("says nothing to somebody who cannot answer it", () => {
    // A guest reads the team's fortnight and posts no face of their own: a
    // question nobody can answer is not a question.
    mood.mayAnswer = false;
    at(17);

    const { result } = ask();

    expect(result.current.show).toBe(false);
    mood.mayAnswer = true;
  });

  it("says nothing once the day has been answered for", () => {
    mood.days = [{ day: TODAY, level: "hard" }];

    const { result } = ask();

    expect(result.current.show).toBe(false);
  });

  it("says nothing on a day one may not answer for", () => {
    // A Saturday carries no today: the domain decides that, not this hook.
    mood.days = [{ day: BEFORE, level: null }];

    const { result } = ask();

    expect(result.current.show).toBe(false);
  });

  it("reaches four o'clock on a tab left open since the morning", () => {
    at(15, 59);
    const { result } = ask();
    expect(result.current.show).toBe(false);

    at(16, 0);
    wait(60_000);

    expect(result.current.show).toBe(true);
  });
});

describe("leaving the reader alone first", () => {
  it("says nothing on the instant one lands somewhere", () => {
    // Whoever has just opened a screen opened it to read it.
    const { result } = renderHook(() => useMoodReminder());

    wait(REMINDER_DELAY_MS - 1_000);

    expect(result.current.show).toBe(false);
  });

  it("waits again at each screen, so nobody is caught on arrival", () => {
    const { result, rerender } = renderHook(() => useMoodReminder());
    wait(REMINDER_DELAY_MS - 1_000);

    pathname.value = "/projects";
    rerender();
    wait(REMINDER_DELAY_MS - 1_000);

    expect(result.current.show).toBe(false);

    wait(1_000);

    expect(result.current.show).toBe(true);
  });

  it("stands once the question has been put", () => {
    // A panel that went back into hiding at every navigation would rise again
    // at the next one, and one that comes and goes reads as a fault.
    const { result, rerender } = ask();
    expect(result.current.show).toBe(true);

    pathname.value = "/projects";
    rerender();

    expect(result.current.show).toBe(true);
  });
});

describe("where the reminder keeps quiet", () => {
  it("never asks on the team screen", () => {
    // Answering there is answering under the eyes of what the answer is about.
    pathname.value = "/mood";

    const { result } = ask();

    expect(result.current.show).toBe(false);
  });

  it("never asks on the home screen, which already carries the check-in", () => {
    pathname.value = "/";

    const { result } = ask();

    expect(result.current.show).toBe(false);
  });
});

describe("turning it down", () => {
  it("is believed for the rest of the day", () => {
    const { result } = ask();

    act(() => result.current.dismiss());

    expect(result.current.show).toBe(false);
  });

  it("asks again the next day", () => {
    window.localStorage.setItem("timesheet.mood-reminder-dismissed", BEFORE);

    const { result } = ask();

    expect(result.current.show).toBe(true);
  });
});

describe("answering from the reminder", () => {
  it("posts for today, and for no other day", () => {
    const { result } = ask();

    result.current.post("excellent");

    expect(mood.post).toHaveBeenCalledWith(TODAY, "excellent");
  });

  it("holds the faces while today's answer travels", () => {
    mood.savingDay = TODAY;

    const { result } = ask();

    expect(result.current.saving).toBe(true);
  });
});

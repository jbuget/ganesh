import { beforeEach, describe, expect, it } from "vitest";
import { act, renderHook } from "@testing-library/react";

import { dismissMoodReminder, useMoodReminderDismissedOn } from "./mood-reminder-store";

const TODAY = "2026-09-23";

describe("turning the reminder down", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("holds nothing until it is turned down", () => {
    const { result } = renderHook(() => useMoodReminderDismissedOn());

    expect(result.current).toBeNull();
  });

  it("remembers the day it was turned down on", () => {
    const { result } = renderHook(() => useMoodReminderDismissedOn());

    act(() => dismissMoodReminder(TODAY));

    expect(result.current).toBe(TODAY);
  });

  it("keeps the refusal in local storage", () => {
    renderHook(() => useMoodReminderDismissedOn());

    act(() => dismissMoodReminder(TODAY));

    expect(window.localStorage.getItem("timesheet.mood-reminder-dismissed")).toBe(
      TODAY,
    );
  });

  it("applies a refusal already saved from the first client render", async () => {
    window.localStorage.setItem("timesheet.mood-reminder-dismissed", TODAY);

    const { result } = renderHook(() => useMoodReminderDismissedOn());
    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current).toBe(TODAY);
  });

  it("notifies every subscriber, so a second tab puts this one straight", () => {
    const first = renderHook(() => useMoodReminderDismissedOn());
    const second = renderHook(() => useMoodReminderDismissedOn());

    act(() => dismissMoodReminder(TODAY));

    expect(first.result.current).toBe(TODAY);
    expect(second.result.current).toBe(TODAY);
  });
});

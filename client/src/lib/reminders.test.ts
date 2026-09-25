import { describe, expect, it } from "vitest";

import { ReminderCadence } from "@/lib/api/generated/model";
import { REMINDER_CHOICES, reminderCadenceLabel } from "@/lib/reminders";

describe("reminderCadenceLabel", () => {
  it("names every cadence in French", () => {
    // A cadence added server-side and left unnamed here would read as a raw
    // « WEEKLY » on somebody's profile.
    const unnamed = Object.values(ReminderCadence).filter(
      (cadence) => reminderCadenceLabel(cadence) === cadence,
    );

    expect(unnamed).toEqual([]);
  });
});

describe("REMINDER_CHOICES", () => {
  it("offers every cadence the domain holds", () => {
    expect(REMINDER_CHOICES.map((choice) => choice.value).sort()).toEqual(
      Object.values(ReminderCadence).sort(),
    );
  });

  it("reads from the most frequent to none at all", () => {
    // « Jamais » closes the list: a way out one reads last, having seen what
    // one would be turning down.
    expect(REMINDER_CHOICES.map((choice) => choice.value)).toEqual([
      ReminderCadence.DAILY,
      ReminderCadence.WEEKLY,
      ReminderCadence.NEVER,
    ]);
  });

  it("says what each cadence means rather than only naming it", () => {
    for (const choice of REMINDER_CHOICES) {
      expect(choice.detail.length).toBeGreaterThan(0);
    }
  });
});

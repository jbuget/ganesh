import { describe, expect, it } from "vitest";

import {
  FULL_TIME,
  daysPerWeek,
  firstOfMonth,
  formatDayValue,
  formatRhythm,
  nextValue,
  patternOf,
  toRequest,
} from "@/lib/rhythm";

describe("what a week adds up to", () => {
  it("counts a full week as five days", () => {
    expect(daysPerWeek(FULL_TIME)).toBe(5);
  });

  it("counts a half day as a half", () => {
    expect(daysPerWeek({ ...FULL_TIME, wednesday: 0.5 })).toBe(4.5);
  });
});

describe("the sentence the reader gets", () => {
  it("agrees in number", () => {
    expect(formatRhythm(FULL_TIME)).toBe("5 jours par semaine");
    expect(formatRhythm({ ...FULL_TIME, wednesday: 0 })).toBe("4 jours par semaine");
  });

  it("spells a half day with a comma, as the grid does", () => {
    expect(formatRhythm({ ...FULL_TIME, wednesday: 0.5 })).toBe(
      "4,5 jours par semaine",
    );
  });

  it("names an absence rather than counting it as nought", () => {
    // « 0 jour par semaine » reads as a figure somebody forgot to fill in.
    // What it says is that nothing is expected of them for now.
    expect(
      formatRhythm({
        monday: 0,
        tuesday: 0,
        wednesday: 0,
        thursday: 0,
        friday: 0,
      }),
    ).toBe("aucun jour travaillé");
  });

  it("says « jour » alone when there is only one", () => {
    expect(
      formatRhythm({
        monday: 1,
        tuesday: 0,
        wednesday: 0,
        thursday: 0,
        friday: 0,
      }),
    ).toBe("1 jour par semaine");
  });

  it("says what one day is worth", () => {
    expect(formatDayValue(1)).toBe("journée entière");
    expect(formatDayValue(0.5)).toBe("demi-journée");
    expect(formatDayValue(0)).toBe("non travaillé");
  });
});

describe("declaring nothing reads as full time", () => {
  it("falls back on a full week", () => {
    expect(patternOf(null)).toEqual(FULL_TIME);
  });
});

describe("clicking a day", () => {
  it("goes down rather than up: one opens it to take days off", () => {
    expect(nextValue(1)).toBe(0.5);
    expect(nextValue(0.5)).toBe(0);
    expect(nextValue(0)).toBe(1);
  });
});

describe("what travels to the API", () => {
  it("carries the five days and the day it opens on", () => {
    expect(toRequest({ ...FULL_TIME, wednesday: 0 }, "2026-09-01")).toEqual({
      monday: 1,
      tuesday: 1,
      wednesday: 0,
      thursday: 1,
      friday: 1,
      effective_from: "2026-09-01",
    });
  });

  it("opens on the first of the month by default", () => {
    expect(firstOfMonth(new Date(2026, 8, 22))).toBe("2026-09-01");
  });
});

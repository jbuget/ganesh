import { describe, expect, it } from "vitest";

import {
  HOURS_IN_A_DAY,
  formatHours,
  toHours,
  valueForKey,
  type DayValue,
} from "./day-value";

describe("toHours", () => {
  it("counts a day as eight hours", () => {
    expect(toHours(1)).toBe(8);
    expect(toHours(0.75)).toBe(6);
    expect(toHours(0.5)).toBe(4);
    expect(toHours(0.25)).toBe(2);
    expect(toHours(0)).toBe(0);
  });

  it("agrees with the constant it is drawn from", () => {
    expect(HOURS_IN_A_DAY).toBe(8);
  });
});

describe("formatHours", () => {
  it("shows nothing for an empty cell", () => {
    // An empty cell means « nothing entered »: a zero would make the grid
    // unreadable.
    expect(formatHours(0)).toBe("");
  });

  it("shows whole hours, which is all the grid can hold", () => {
    expect(formatHours(0.25)).toBe("2");
    expect(formatHours(0.5)).toBe("4");
    expect(formatHours(0.75)).toBe("6");
    expect(formatHours(1)).toBe("8");
  });

  /** A day total is a sum of cells, and it can run past one day. */
  it("adds up past a day for a total", () => {
    expect(formatHours(1.5)).toBe("12");
    expect(formatHours(2)).toBe("16");
  });

  it("shows a half hour rather than rounding it away", () => {
    // No cell can hold one, but an inherited total might: showing « 3 » for
    // 3.5 would report a figure the register does not hold.
    expect(formatHours(0.4375)).toBe("3,5");
  });
});

describe("valueForKey", () => {
  it("reads the hours one types", () => {
    expect(valueForKey("2")).toBe(0.25);
    expect(valueForKey("4")).toBe(0.5);
    expect(valueForKey("6")).toBe(0.75);
    expect(valueForKey("8")).toBe(1);
  });

  it("empties the cell on a zero, and on the keys that erase", () => {
    expect(valueForKey("0")).toBe(0);
    expect(valueForKey("Backspace")).toBe(0);
    expect(valueForKey("Delete")).toBe(0);
  });

  it("reads nothing out of an hour the day does not divide into", () => {
    for (const key of ["1", "3", "5", "7", "9", "a", "Enter", " "]) {
      expect(valueForKey(key)).toBeNull();
    }
  });

  it("hands back a value the grid holds", () => {
    const written: DayValue | null = valueForKey("6");
    expect(written).toBe(0.75);
  });
});

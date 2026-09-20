import { describe, expect, it } from "vitest";

import { ACTIVITY_RANGES, formatDays, formatMovement } from "./activity";

describe("activity windows", () => {
  it("offers anchored windows only", () => {
    // A rolling week straddles two weeks; « la semaine dernière » does not.
    expect(ACTIVITY_RANGES.map((range) => range.value)).toEqual([
      "this_week",
      "last_week",
      "last_two_weeks",
      "this_month",
      "last_month",
    ]);
  });
});

describe("formatDays", () => {
  it("draws nothing declared as an em dash, never as a zero", () => {
    expect(formatDays(0)).toBe("—");
  });

  it("says a half day the French way", () => {
    expect(formatDays(0.5)).toBe("0,5");
  });

  it("drops a trailing zero", () => {
    expect(formatDays(3)).toBe("3");
  });
});

describe("formatMovement", () => {
  it("says nothing when the line did not move", () => {
    // A « +0 j » would claim a stability that is only an absence of change.
    expect(formatMovement(0)).toBeNull();
  });

  it("signs a rise", () => {
    expect(formatMovement(2.5)).toBe("+2,5 j");
  });

  it("uses a true minus sign for a fall", () => {
    expect(formatMovement(-3)).toBe("−3 j");
  });
});

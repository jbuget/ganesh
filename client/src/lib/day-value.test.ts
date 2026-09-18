import { describe, expect, it } from "vitest";

import { cycleDayValue } from "./day-value";

describe("cycleDayValue", () => {
  it("moves from empty to a full day", () => {
    expect(cycleDayValue(0)).toBe(1);
  });

  it("moves from a full day to a half day", () => {
    expect(cycleDayValue(1)).toBe(0.5);
  });

  it("returns to empty after a half day", () => {
    expect(cycleDayValue(0.5)).toBe(0);
  });

  it("loops in three clicks", () => {
    expect(cycleDayValue(cycleDayValue(cycleDayValue(0)))).toBe(0);
  });
});

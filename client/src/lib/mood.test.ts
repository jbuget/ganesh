import { describe, expect, it } from "vitest";

import { MOODS, dayLabel, mood } from "./mood";

describe("mood", () => {
  it("offers the levels from the best to the worst", () => {
    expect(MOODS.map((level) => level.value)).toEqual([
      "excellent",
      "good",
      "neutral",
      "hard",
      "bad",
    ]);
  });

  it("gives every level a mark of its own", () => {
    const shades = new Set(MOODS.map((level) => level.colour));

    expect(shades.size).toBe(MOODS.length);
  });

  it("names a level", () => {
    expect(mood("bad")?.label).toBe("Mauvaise");
  });

  it("names nothing when nothing was answered", () => {
    expect(mood(null)).toBeNull();
  });
});

describe("dayLabel", () => {
  it("calls today today", () => {
    expect(dayLabel("2026-09-15", "2026-09-15")).toBe("Aujourd'hui");
  });

  it("names the other day rather than calling it yesterday", () => {
    expect(dayLabel("2026-09-11", "2026-09-14")).toBe("vendredi 11 sept.");
  });
});

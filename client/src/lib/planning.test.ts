import { describe, expect, it } from "vitest";

import { blocker, fillRatio, slippage, slippageLabel } from "./planning";

describe("slippage", () => {
  it("reads a landing well past the date announced as late", () => {
    expect(slippage(9)).toBe("late");
  });

  it("reads a landing well ahead of it as early", () => {
    expect(slippage(-9)).toBe("early");
  });

  it("forgives a day or two either side", () => {
    // A projection is not a commitment: crying « en retard d'un jour » would
    // teach everyone to stop reading the column.
    expect(slippage(2)).toBe("on-time");
    expect(slippage(-2)).toBe("on-time");
  });

  it("says nothing of a mission with no date announced", () => {
    expect(slippage(null)).toBe("none");
  });
});

describe("slippageLabel", () => {
  it("counts the days late", () => {
    expect(slippageLabel(5)).toBe("5 jours de retard");
  });

  it("counts the days early", () => {
    expect(slippageLabel(-5)).toBe("5 jours d'avance");
  });

  it("keeps a single day singular", () => {
    expect(slippageLabel(3)).toBe("3 jours de retard");
    expect(slippageLabel(-3)).toBe("3 jours d'avance");
  });

  it("says a landing inside the tolerance is on time", () => {
    expect(slippageLabel(1)).toBe("Dans les temps");
  });
});

describe("blocker", () => {
  it("names what to do about it, not just what is wrong", () => {
    expect(blocker("no_estimate")?.hint).toContain("Estimez");
    expect(blocker("no_assignee")?.hint).toContain("Affectez");
  });

  it("says nothing of a mission that could be planned", () => {
    expect(blocker(null)).toBeNull();
  });
});

describe("fillRatio", () => {
  it("adds what is declared to what is projected", () => {
    expect(fillRatio(5, 2, 1)).toBeCloseTo(0.6);
  });

  it("goes past one on an over-booked week", () => {
    expect(fillRatio(5, 4, 2)).toBeCloseTo(1.2);
  });

  it("stays at nothing on a week with no working day", () => {
    expect(fillRatio(0, 0, 0)).toBe(0);
  });
});

import { describe, expect, it } from "vitest";

import { isMilestoneLate } from "./milestones";

const TODAY = new Date("2026-09-25T10:00:00");

describe("isMilestoneLate", () => {
  it("reads a day still to come as on time", () => {
    expect(isMilestoneLate("2026-11-30", null, TODAY)).toBe(false);
  });

  it("reads the day itself as on time", () => {
    // Late on the day one announced would be harsh: the day is not over.
    expect(isMilestoneLate("2026-09-25", null, TODAY)).toBe(false);
  });

  it("reads a day gone by with nothing reached as late", () => {
    expect(isMilestoneLate("2026-06-30", null, TODAY)).toBe(true);
  });

  /**
   * A milestone that happened is a fact, whatever day it happened on. Reading
   * it as late would leave a red mark on everything the team ever delivered
   * a week after it said it would.
   */
  it("never calls a milestone that was reached late", () => {
    expect(isMilestoneLate("2026-06-30", "2026-07-15", TODAY)).toBe(false);
  });
});

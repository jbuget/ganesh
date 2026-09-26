import { describe, expect, it } from "vitest";

import { isGoLiveLate } from "./go-live";

const TODAY = new Date("2026-09-25T10:00:00");

describe("isGoLiveLate", () => {
  it("says nothing of a mission nobody has dated", () => {
    expect(isGoLiveLate(null, "development", TODAY)).toBe(false);
  });

  it("reads a day still to come as on time", () => {
    expect(isGoLiveLate("2026-11-30", "development", TODAY)).toBe(false);
  });

  it("reads the day itself as on time", () => {
    // Late on the day one announced would be harsh: the day is not over.
    expect(isGoLiveLate("2026-09-25", "development", TODAY)).toBe(false);
  });

  it("reads a day gone by as late", () => {
    expect(isGoLiveLate("2026-06-30", "development", TODAY)).toBe(true);
  });

  /**
   * A service already running has landed. Reading it as late would put a red
   * mark on every mission the team delivered after its announced day, for as
   * long as it lives.
   */
  it("never calls a service in operations late", () => {
    expect(isGoLiveLate("2026-06-30", "operations", TODAY)).toBe(false);
  });
});

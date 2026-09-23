import { describe, expect, it } from "vitest";

import { AuditAction } from "@/lib/api/generated/model";
import {
  ACTION_FAMILIES,
  NO_FILTER,
  everyOfferedAction,
  hasAnyFilter,
} from "@/lib/audit-filters";

describe("the gestures the filter offers", () => {
  /**
   * A gesture the register writes and the picker does not offer cannot be
   * looked for — and nothing says so: the list simply reads as complete.
   */
  it("offers every gesture the register writes", () => {
    const offered = new Set<string>(everyOfferedAction());
    const missing = Object.values(AuditAction).filter((action) => !offered.has(action));

    expect(missing).toEqual([]);
  });

  /** Offering one twice would tick two boxes on one click. */
  it("offers each of them once", () => {
    const offered = everyOfferedAction();

    expect(offered).toHaveLength(new Set(offered).size);
  });

  it("names every family it groups them under", () => {
    for (const family of ACTION_FAMILIES) {
      expect(family.label).not.toBe("");
      expect(family.actions.length).toBeGreaterThan(0);
    }
  });
});

describe("hasAnyFilter", () => {
  it("reads an untouched bar as filtering nothing", () => {
    expect(hasAnyFilter(NO_FILTER)).toBe(false);
  });

  it("reads one criterion as enough", () => {
    expect(hasAnyFilter({ ...NO_FILTER, actions: ["project.delete"] })).toBe(true);
    expect(hasAnyFilter({ ...NO_FILTER, actorIds: ["3"] })).toBe(true);
    expect(hasAnyFilter({ ...NO_FILTER, fromDay: "2026-09-01" })).toBe(true);
    expect(hasAnyFilter({ ...NO_FILTER, toDay: "2026-09-30" })).toBe(true);
  });
});

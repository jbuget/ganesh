import { describe, expect, it } from "vitest";

import type { MonthGridResponse } from "@/lib/api/generated/model";
import { pendingCell, pendingKey, withPendingEntries } from "./pending-entries";

const TODAY = "2026-09-15";

function grid(overrides: Partial<MonthGridResponse> = {}): MonthGridResponse {
  return {
    user_id: 1,
    month: "2026-09-01",
    days: [],
    rows: [
      {
        project_id: 10,
        label: "Portail",
        kind: "project",
        estimated_days: 20,
        values: { "2026-09-14": 0.5 },
        actual_total: 0.5,
        forecast_total: 0,
        total: 0.5,
        total_consumed_days: 12.5,
      },
    ],
    day_totals: [
      { day: "2026-09-14", total: 0.5, exceeds_capacity: false },
      { day: "2026-09-16", total: 0, exceeds_capacity: false },
    ],
    working_days: 22,
    is_writable: true,
    actual_total: 0.5,
    forecast_total: 0,
    ...overrides,
  } as MonthGridResponse;
}

const cell = { userId: 1, projectId: 10, activityId: null, day: "2026-09-14" };

describe("the key a waiting cell is held under", () => {
  it("reads back the cell it names", () => {
    expect(pendingCell(pendingKey(cell))).toEqual(cell);
  });
});

describe("laying waiting cells over the grid", () => {
  it("gives the grid back untouched when nothing is waiting", () => {
    const month = grid();

    expect(withPendingEntries(month, {}, TODAY)).toBe(month);
  });

  /** The cycle reads the cell: a second click must see the first. */
  it("shows the value clicked rather than the one the server holds", () => {
    const shown = withPendingEntries(grid(), { [pendingKey(cell)]: 1 }, TODAY);

    expect(shown.rows[0].values["2026-09-14"]).toBe(1);
  });

  it("empties a cell rather than writing a zero into it", () => {
    const shown = withPendingEntries(grid(), { [pendingKey(cell)]: 0 }, TODAY);

    expect(shown.rows[0].values).not.toHaveProperty("2026-09-14");
  });

  /**
   * The day's total carries a colour, and it is what one watches while
   * clicking a second time: a total left behind would call a day incomplete
   * that has just been completed.
   */
  it("moves the totals with the cell, the day's as much as the month's", () => {
    const shown = withPendingEntries(grid(), { [pendingKey(cell)]: 1 }, TODAY);

    expect(shown.rows[0].total).toBe(1);
    expect(shown.rows[0].actual_total).toBe(1);
    expect(shown.rows[0].total_consumed_days).toBe(13);
    expect(shown.day_totals[0].total).toBe(1);
    expect(shown.actual_total).toBe(1);
  });

  it("says a day goes over capacity as soon as it does", () => {
    // Half a day already stands on another project that same day.
    const month = grid({
      day_totals: [
        { day: "2026-09-14", total: 1, exceeds_capacity: false },
        { day: "2026-09-16", total: 0, exceeds_capacity: false },
      ],
    });

    const shown = withPendingEntries(month, { [pendingKey(cell)]: 1 }, TODAY);

    expect(shown.day_totals[0].total).toBe(1.5);
    expect(shown.day_totals[0].exceeds_capacity).toBe(true);
  });

  it("counts a day ahead of today as forecast, and never as consumed", () => {
    const ahead = { ...cell, day: "2026-09-16" };

    const shown = withPendingEntries(grid(), { [pendingKey(ahead)]: 1 }, TODAY);

    expect(shown.rows[0].forecast_total).toBe(1);
    expect(shown.rows[0].actual_total).toBe(0.5);
    expect(shown.rows[0].total_consumed_days).toBe(12.5);
    expect(shown.forecast_total).toBe(1);
  });

  /**
   * One walks to a colleague's month with a write still waiting. Read under
   * the wrong name, it would paint a day they never declared.
   */
  it("leaves alone a cell waiting on somebody else's month", () => {
    const elsewhere = { ...cell, userId: 7 };

    const shown = withPendingEntries(grid(), { [pendingKey(elsewhere)]: 1 }, TODAY);

    expect(shown.rows[0].values["2026-09-14"]).toBe(0.5);
    expect(shown.day_totals[0].total).toBe(0.5);
  });

  it("leaves alone a row the grid no longer carries", () => {
    const gone = { ...cell, projectId: 99 };

    const shown = withPendingEntries(grid(), { [pendingKey(gone)]: 1 }, TODAY);

    expect(shown.rows[0].total).toBe(0.5);
    expect(shown.actual_total).toBe(0.5);
  });
});

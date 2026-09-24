import { describe, expect, it } from "vitest";

import { countCompleteDays } from "@/lib/month-completion";

const DAYS = [
  { day: "2026-09-01", is_off_day: false },
  { day: "2026-09-02", is_off_day: false },
  { day: "2026-09-03", is_off_day: false },
  { day: "2026-09-05", is_off_day: true },
];

describe("countCompleteDays", () => {
  it("counts the working days whose entries add up to a whole day", () => {
    const totals = [
      { day: "2026-09-01", total: 1 },
      { day: "2026-09-02", total: 1 },
      { day: "2026-09-03", total: 0.75 },
    ];

    expect(countCompleteDays(DAYS, totals)).toBe(2);
  });

  it("does not count a day nothing was entered on", () => {
    expect(countCompleteDays(DAYS, [{ day: "2026-09-01", total: 1 }])).toBe(1);
  });

  /**
   * A day over one is no more complete than a day under it: both are days to
   * go back to, which is the whole point of the count.
   */
  it("does not count a day carrying more than a day", () => {
    const totals = [
      { day: "2026-09-01", total: 2 },
      { day: "2026-09-02", total: 1 },
    ];

    expect(countCompleteDays(DAYS, totals)).toBe(1);
  });

  /**
   * A Saturday somebody declared on is inherited data the grid keeps visible,
   * but it is not one of the month's working days and cannot make the count
   * pass the total it is read against.
   */
  it("leaves a non-working day out, whatever was entered on it", () => {
    const totals = [
      { day: "2026-09-05", total: 1 },
      { day: "2026-09-01", total: 1 },
    ];

    expect(countCompleteDays(DAYS, totals)).toBe(1);
  });

  it("counts nothing on an empty month", () => {
    expect(countCompleteDays(DAYS, [])).toBe(0);
  });
});

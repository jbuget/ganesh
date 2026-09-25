import { describe, expect, it } from "vitest";

import {
  dayNumber,
  firstDayOfMonth,
  formatShortDate,
  formatDecimalDays,
  formatTotal,
  formatMonth,
  monthParam,
  nextMonth,
  parseMonthParam,
  previousMonth,
  weekdayInitial,
} from "./dates";

describe("firstDayOfMonth", () => {
  it("pads the month to two digits", () => {
    expect(firstDayOfMonth(2026, 9)).toBe("2026-09-01");
  });
});

describe("formatMonth", () => {
  it("names the month in French", () => {
    expect(formatMonth(2026, 9)).toBe("septembre 2026");
  });

  it("handles the accents of the month of August", () => {
    expect(formatMonth(2026, 8)).toBe("août 2026");
  });
});

describe("moving from month to month", () => {
  it("goes back to the previous month", () => {
    expect(previousMonth(2026, 9)).toEqual({ year: 2026, month: 8 });
  });

  it("goes back a year in January", () => {
    expect(previousMonth(2026, 1)).toEqual({ year: 2025, month: 12 });
  });

  it("moves on to the next month", () => {
    expect(nextMonth(2026, 9)).toEqual({ year: 2026, month: 10 });
  });

  it("moves on a year in December", () => {
    expect(nextMonth(2026, 12)).toEqual({ year: 2027, month: 1 });
  });
});

describe("dayNumber", () => {
  it("extracts the day number", () => {
    expect(dayNumber("2026-09-15")).toBe(15);
  });
});

describe("weekdayInitial", () => {
  it("recognises a Tuesday", () => {
    expect(weekdayInitial("2026-09-15")).toBe("M");
  });

  it("recognises a Saturday", () => {
    expect(weekdayInitial("2026-09-12")).toBe("S");
  });

  it("recognises a Sunday", () => {
    expect(weekdayInitial("2026-09-13")).toBe("D");
  });
});

describe("formatTotal", () => {
  it("shows zero rather than a blank", () => {
    expect(formatTotal(0)).toBe("0");
  });

  it("shows a half day in decimal, as the days beside it are written", () => {
    // « ½ » went with the grid's cells, which now read in hours. A total
    // counts days, and says so the way every other day count does.
    expect(formatTotal(0.5)).toBe("0,5");
  });

  it("shows a total with a half day", () => {
    expect(formatTotal(2.5)).toBe("2,5");
  });
});

describe("formatDecimalDays", () => {
  it("writes a half day in decimal, the French way", () => {
    expect(formatDecimalDays(7.5)).toBe("7,5");
  });

  it("leaves a whole number without a needless decimal", () => {
    expect(formatDecimalDays(26)).toBe("26");
  });

  it("keeps the zero visible", () => {
    expect(formatDecimalDays(0)).toBe("0");
  });

  it("writes a half day on its own", () => {
    expect(formatDecimalDays(0.5)).toBe("0,5");
  });

  /**
   * A quarter of a day is 0.25, and a decimal is not enough to say it: rounded
   * to one, it came out « 0,3 » and three quarters « 0,8 » — figures the
   * register never held.
   */
  it("writes a quarter of a day whole", () => {
    expect(formatDecimalDays(0.25)).toBe("0,25");
    expect(formatDecimalDays(0.75)).toBe("0,75");
    expect(formatDecimalDays(8.25)).toBe("8,25");
  });

  it("drops a trailing zero rather than writing « 8,50 »", () => {
    expect(formatDecimalDays(8.5)).toBe("8,5");
  });

  /** An average is not a declared day: two decimals are where it stops. */
  it("stops at two decimals for a figure that is not a quarter", () => {
    expect(formatDecimalDays(7.333)).toBe("7,33");
  });
});

describe("formatShortDate", () => {
  it("writes an ISO date as day/month/year", () => {
    expect(formatShortDate("2026-09-18")).toBe("18/09/2026");
  });

  it("ignores the time of a timestamp", () => {
    expect(formatShortDate("2026-09-18T00:36:07.943722")).toBe("18/09/2026");
  });
});

describe("monthParam / parseMonthParam", () => {
  it("names a month the way an address carries it", () => {
    expect(monthParam({ year: 2026, month: 8 })).toBe("2026-08");
  });

  it("reads back what it wrote", () => {
    expect(parseMonthParam("2026-08")).toEqual({ year: 2026, month: 8 });
  });

  it("ignores an address naming no month", () => {
    expect(parseMonthParam(null)).toBeNull();
  });

  it("ignores what is not a month: a hand-typed address must not break the screen", () => {
    expect(parseMonthParam("septembre")).toBeNull();
    expect(parseMonthParam("2026-13")).toBeNull();
    expect(parseMonthParam("2026-00")).toBeNull();
  });
});

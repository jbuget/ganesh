import { describe, expect, it } from "vitest";

import {
  dayNumber,
  firstDayOfMonth,
  formatDateCourte,
  formatDays,
  formatDecimalDays,
  formatTotal,
  formatMonth,
  nextMonth,
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

describe("navigation entre mois", () => {
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

describe("formatDays", () => {
  it("shows nothing for a null value", () => {
    expect(formatDays(0)).toBe("");
  });

  it("shows a half day", () => {
    expect(formatDays(0.5)).toBe("½");
  });

  it("shows a whole day", () => {
    expect(formatDays(1)).toBe("1");
  });

  it("shows a total with a half day", () => {
    expect(formatDays(3.5)).toBe("3½");
  });
});

describe("formatTotal", () => {
  it("shows zero rather than a blank", () => {
    expect(formatTotal(0)).toBe("0");
  });

  it("shows a half day as a cell does", () => {
    expect(formatTotal(0.5)).toBe("½");
  });

  it("shows a total with a half day", () => {
    expect(formatTotal(2.5)).toBe("2½");
  });
});

describe("formatJoursDecimal", () => {
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
});

describe("formatDateCourte", () => {
  it("writes an ISO date as day/month/year", () => {
    expect(formatDateCourte("2026-09-18")).toBe("18/09/2026");
  });

  it("ignores the time of a timestamp", () => {
    expect(formatDateCourte("2026-09-18T00:36:07.943722")).toBe("18/09/2026");
  });
});

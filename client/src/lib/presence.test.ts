import { describe, expect, it } from "vitest";

import {
  AT_THE_OFFICE,
  daysOnSite,
  daysPresent,
  nextDay,
  sayDay,
  sayWeek,
  weekOf,
} from "@/lib/presence";

describe("what a day says", () => {
  it("names the place the team already names", () => {
    expect(sayDay("ON_SITE")).toBe("sur site");
    expect(sayDay("REMOTE")).toBe("télétravail");
    expect(sayDay("AWAY")).toBe("absent");
  });

  it("walks the three states and comes back round", () => {
    expect(nextDay("ON_SITE")).toBe("REMOTE");
    expect(nextDay("REMOTE")).toBe("AWAY");
    expect(nextDay("AWAY")).toBe("ON_SITE");
  });
});

describe("counting the week", () => {
  const week = { ...AT_THE_OFFICE, wednesday: "REMOTE", friday: "AWAY" } as const;

  it("counts the office and the days worked apart", () => {
    expect(daysOnSite(week)).toBe(3);
    expect(daysPresent(week)).toBe(4);
  });

  it("says the week the way somebody would", () => {
    expect(sayWeek(week)).toBe("3 jours sur site sur 4");
  });

  it("agrees in number", () => {
    expect(
      sayWeek({
        ...AT_THE_OFFICE,
        tuesday: "AWAY",
        wednesday: "AWAY",
        thursday: "AWAY",
        friday: "AWAY",
      }),
    ).toBe("1 jour sur site sur 1");
  });

  it("says a week spent entirely at home without counting an office day", () => {
    expect(
      sayWeek({
        monday: "REMOTE",
        tuesday: "REMOTE",
        wednesday: "REMOTE",
        thursday: "REMOTE",
        friday: "REMOTE",
      }),
    ).toBe("5 jours en télétravail");
  });

  it("says a week away outright", () => {
    expect(
      sayWeek({
        monday: "AWAY",
        tuesday: "AWAY",
        wednesday: "AWAY",
        thursday: "AWAY",
        friday: "AWAY",
      }),
    ).toBe("absent toute la semaine");
  });
});

describe("a week nobody declared", () => {
  it("starts from a week at the office, which is where most weeks start", () => {
    expect(weekOf(null)).toEqual(AT_THE_OFFICE);
  });
});

import { describe, expect, it } from "vitest";

import {
  dayNumber,
  firstDayOfMonth,
  formatDays,
  formatMonth,
  nextMonth,
  previousMonth,
  weekdayInitial,
} from "./dates";

describe("firstDayOfMonth", () => {
  it("complète le mois sur deux chiffres", () => {
    expect(firstDayOfMonth(2026, 9)).toBe("2026-09-01");
  });
});

describe("formatMonth", () => {
  it("nomme le mois en français", () => {
    expect(formatMonth(2026, 9)).toBe("septembre 2026");
  });

  it("gère les accents du mois d'août", () => {
    expect(formatMonth(2026, 8)).toBe("août 2026");
  });
});

describe("navigation entre mois", () => {
  it("recule dans le mois précédent", () => {
    expect(previousMonth(2026, 9)).toEqual({ year: 2026, month: 8 });
  });

  it("recule d'une année en janvier", () => {
    expect(previousMonth(2026, 1)).toEqual({ year: 2025, month: 12 });
  });

  it("avance dans le mois suivant", () => {
    expect(nextMonth(2026, 9)).toEqual({ year: 2026, month: 10 });
  });

  it("avance d'une année en décembre", () => {
    expect(nextMonth(2026, 12)).toEqual({ year: 2027, month: 1 });
  });
});

describe("dayNumber", () => {
  it("extrait le numéro du jour", () => {
    expect(dayNumber("2026-09-15")).toBe(15);
  });
});

describe("weekdayInitial", () => {
  it("reconnaît un mardi", () => {
    expect(weekdayInitial("2026-09-15")).toBe("M");
  });

  it("reconnaît un samedi", () => {
    expect(weekdayInitial("2026-09-12")).toBe("S");
  });

  it("reconnaît un dimanche", () => {
    expect(weekdayInitial("2026-09-13")).toBe("D");
  });
});

describe("formatDays", () => {
  it("n'affiche rien pour une valeur nulle", () => {
    expect(formatDays(0)).toBe("");
  });

  it("affiche une demi-journée", () => {
    expect(formatDays(0.5)).toBe("½");
  });

  it("affiche une journée entière", () => {
    expect(formatDays(1)).toBe("1");
  });

  it("affiche un total avec demi-journée", () => {
    expect(formatDays(3.5)).toBe("3½");
  });
});

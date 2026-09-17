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

describe("formatTotal", () => {
  it("affiche zéro plutôt qu'un blanc", () => {
    expect(formatTotal(0)).toBe("0");
  });

  it("affiche une demi-journée comme une cellule", () => {
    expect(formatTotal(0.5)).toBe("½");
  });

  it("affiche un total avec demi-journée", () => {
    expect(formatTotal(2.5)).toBe("2½");
  });
});

describe("formatJoursDecimal", () => {
  it("écrit une demi-journée en décimal, à la française", () => {
    expect(formatDecimalDays(7.5)).toBe("7,5");
  });

  it("laisse un entier sans décimale inutile", () => {
    expect(formatDecimalDays(26)).toBe("26");
  });

  it("garde le zéro visible", () => {
    expect(formatDecimalDays(0)).toBe("0");
  });

  it("écrit une demi-journée seule", () => {
    expect(formatDecimalDays(0.5)).toBe("0,5");
  });
});

describe("formatDateCourte", () => {
  it("écrit une date ISO en jour/mois/année", () => {
    expect(formatDateCourte("2026-09-18")).toBe("18/09/2026");
  });

  it("ignore l'heure d'un horodatage", () => {
    expect(formatDateCourte("2026-09-18T00:36:07.943722")).toBe("18/09/2026");
  });
});

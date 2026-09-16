import { describe, expect, it } from "vitest";

import { cycleDayValue } from "./day-value";

describe("cycleDayValue", () => {
  it("passe de vide à une journée complète", () => {
    expect(cycleDayValue(0)).toBe(1);
  });

  it("passe d'une journée complète à une demi-journée", () => {
    expect(cycleDayValue(1)).toBe(0.5);
  });

  it("revient à vide après une demi-journée", () => {
    expect(cycleDayValue(0.5)).toBe(0);
  });

  it("boucle en trois clics", () => {
    expect(cycleDayValue(cycleDayValue(cycleDayValue(0)))).toBe(0);
  });
});

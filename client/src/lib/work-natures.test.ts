import { describe, expect, it } from "vitest";

import { WORK_NATURES, workNatureLabel } from "./work-natures";

describe("WORK_NATURES", () => {
  it("offers every trade, in French, in the order they are read", () => {
    expect(WORK_NATURES.map((nature) => nature.label)).toEqual([
      "Développement",
      "Design",
      "Pilotage",
      "Data",
      "Paramétrage",
      "Accompagnement",
      "Coaching",
    ]);
  });
});

describe("workNatureLabel", () => {
  it("names a trade in French", () => {
    expect(workNatureLabel("user_enablement")).toBe("Accompagnement");
  });

  it("names nothing when no trade was stated", () => {
    expect(workNatureLabel(null)).toBeNull();
  });
});

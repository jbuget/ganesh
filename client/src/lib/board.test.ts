import { describe, expect, it } from "vitest";

import { progress, category, phaseLabel, PHASES, phaseRank } from "./board";

describe("PHASES", () => {
  it("follows the life cycle of a project", () => {
    expect(PHASES.map((p) => p.status)).toEqual([
      "exploration",
      "scoping",
      "development",
      "validation",
      "deployment",
      "operations",
    ]);
  });

  it("names each phase in French", () => {
    expect(phaseLabel("deployment")).toBe("Déploiement");
  });
});

describe("phaseRank", () => {
  it("ranks the phases in kanban column order", () => {
    expect(phaseRank("scoping")).toBeLessThan(phaseRank("development"));
    expect(phaseRank("development")).toBeLessThan(phaseRank("operations"));
  });

  it("sends what carries no phase to the end of the list", () => {
    expect(phaseRank(null)).toBeGreaterThan(phaseRank("operations"));
  });
});

describe("categorie", () => {
  it("gives the label and the shade of an axis", () => {
    expect(category("innovate_differentiate")?.label).toBe("Innover & différencier");
  });

  it("returns nothing for a mission with no axis", () => {
    expect(category(null)).toBeNull();
  });
});

describe("avancement", () => {
  it("passes no judgement on a mission with no estimate", () => {
    expect(progress(12, null)).toBe("sans-estime");
  });

  it("stays quiet while the budget is far off", () => {
    expect(progress(5, 20)).toBe("en-cours");
  });

  it("warns when the budget draws near", () => {
    expect(progress(16, 20)).toBe("proche");
  });

  it("flags an overrun", () => {
    expect(progress(21, 20)).toBe("depasse");
  });

  it("treats a budget just reached as still held", () => {
    expect(progress(20, 20)).toBe("proche");
  });
});

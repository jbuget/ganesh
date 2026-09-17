import { describe, expect, it } from "vitest";

import { progress, category, phaseLabel, PHASES, phaseRank } from "./board";

describe("PHASES", () => {
  it("suit le cycle de vie d'un projet", () => {
    expect(PHASES.map((p) => p.status)).toEqual([
      "exploration",
      "scoping",
      "build",
      "validation",
      "deployment",
      "operations",
    ]);
  });

  it("nomme chaque phase en français", () => {
    expect(phaseLabel("deployment")).toBe("Déploiement");
  });
});

describe("phaseRank", () => {
  it("classe les phases dans l'ordre des colonnes du kanban", () => {
    expect(phaseRank("scoping")).toBeLessThan(phaseRank("build"));
    expect(phaseRank("build")).toBeLessThan(phaseRank("operations"));
  });

  it("renvoie en fin de liste ce qui ne porte pas de phase", () => {
    expect(phaseRank(null)).toBeGreaterThan(phaseRank("operations"));
  });
});

describe("categorie", () => {
  it("donne le libellé et la teinte d'un axe", () => {
    expect(category("innovate_differentiate")?.label).toBe("Innover & différencier");
  });

  it("ne renvoie rien pour une mission sans axe", () => {
    expect(category(null)).toBeNull();
  });
});

describe("avancement", () => {
  it("ne juge pas une mission sans estimé", () => {
    expect(progress(12, null)).toBe("sans-estime");
  });

  it("reste discret tant qu'on est loin du budget", () => {
    expect(progress(5, 20)).toBe("en-cours");
  });

  it("alerte quand on approche du budget", () => {
    expect(progress(16, 20)).toBe("proche");
  });

  it("signale un dépassement", () => {
    expect(progress(21, 20)).toBe("depasse");
  });

  it("considère le budget atteint comme encore tenu", () => {
    expect(progress(20, 20)).toBe("proche");
  });
});

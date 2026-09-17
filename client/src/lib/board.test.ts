import { describe, expect, it } from "vitest";

import {
  avancement,
  categorie,
  formatMiseEnService,
  libellePhase,
  PHASES,
} from "./board";

describe("PHASES", () => {
  it("suit le cycle de vie d'un projet", () => {
    expect(PHASES.map((p) => p.statut)).toEqual([
      "exploration",
      "cadrage",
      "realisation",
      "validation",
      "deploiement",
      "exploitation",
    ]);
  });

  it("nomme chaque phase en français", () => {
    expect(libellePhase("deploiement")).toBe("Déploiement");
  });
});

describe("categorie", () => {
  it("donne le libellé et la teinte d'un axe", () => {
    expect(categorie("innover_differencier")?.libelle).toBe("Innover & différencier");
  });

  it("ne renvoie rien pour une mission sans axe", () => {
    expect(categorie(null)).toBeNull();
  });
});

describe("formatMiseEnService", () => {
  it("écrit la date en toutes lettres", () => {
    expect(formatMiseEnService("2026-11-15")).toBe("15 nov. 2026");
  });

  it("ne renvoie rien quand aucune date n'est prévue", () => {
    expect(formatMiseEnService(null)).toBeNull();
  });
});

describe("avancement", () => {
  it("ne juge pas une mission sans estimé", () => {
    expect(avancement(12, null)).toBe("sans-estime");
  });

  it("reste discret tant qu'on est loin du budget", () => {
    expect(avancement(5, 20)).toBe("en-cours");
  });

  it("alerte quand on approche du budget", () => {
    expect(avancement(16, 20)).toBe("proche");
  });

  it("signale un dépassement", () => {
    expect(avancement(21, 20)).toBe("depasse");
  });

  it("considère le budget atteint comme encore tenu", () => {
    expect(avancement(20, 20)).toBe("proche");
  });
});

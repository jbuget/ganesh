import { describe, expect, it } from "vitest";

import { parseProjectsCsv } from "./csv-import";

describe("parseProjectsCsv", () => {
  it("lit un fichier séparé par des points-virgules", () => {
    const lines = parseProjectsCsv("label;estime_j\nPortail;20");

    expect(lines).toHaveLength(1);
    expect(lines[0].label).toBe("Portail");
    expect(lines[0].estimated_days).toBe(20);
  });

  it("lit aussi un fichier séparé par des virgules", () => {
    const lines = parseProjectsCsv("label,estime_j\nPortail,20");

    expect(lines[0].label).toBe("Portail");
    expect(lines[0].estimated_days).toBe(20);
  });

  it("se moque de l'ordre des colonnes", () => {
    const lines = parseProjectsCsv("estime_j;label\n30;Extranet");

    expect(lines[0].label).toBe("Extranet");
    expect(lines[0].estimated_days).toBe(30);
  });

  it("ignore les colonnes qu'il ne connaît pas", () => {
    const lines = parseProjectsCsv("label;Service / BU;estime_j\nPortail;DSI;20");

    expect(lines[0].label).toBe("Portail");
    expect(lines[0].estimated_days).toBe(20);
  });

  it("accepte une virgule décimale", () => {
    expect(parseProjectsCsv("label;estime_j\nPortail;7,5")[0].estimated_days).toBe(7.5);
  });

  it("laisse l'estimé vide plutôt que d'inventer un zéro", () => {
    expect(parseProjectsCsv("label;estime_j\nPortail;")[0].estimated_days).toBeNull();
  });

  it("rattache un lot à son projet par le libellé", () => {
    const lines = parseProjectsCsv("label;kind;parent_label\nLot API;lot;Portail");

    expect(lines[0].kind).toBe("work_package");
    expect(lines[0].parent_label).toBe("Portail");
  });

  it("considère une mission comme un projet par défaut", () => {
    expect(parseProjectsCsv("label\nPortail")[0].kind).toBe("project");
  });

  it("retire les guillemets d'encadrement", () => {
    expect(parseProjectsCsv('label\n"Portail bailleurs"')[0].label).toBe(
      "Portail bailleurs",
    );
  });

  it("ignore les lignes vides", () => {
    expect(parseProjectsCsv("label\nPortail\n\n\nExtranet")).toHaveLength(2);
  });

  it("ne renvoie rien pour un fichier sans donnée", () => {
    expect(parseProjectsCsv("label;estime_j")).toEqual([]);
    expect(parseProjectsCsv("")).toEqual([]);
  });
});

import { describe, expect, it } from "vitest";

import { parseProjectsCsv } from "./csv-import";

describe("parseProjectsCsv", () => {
  it("lit un fichier séparé par des points-virgules", () => {
    const lignes = parseProjectsCsv("label;estime_j\nPortail;20");

    expect(lignes).toHaveLength(1);
    expect(lignes[0].label).toBe("Portail");
    expect(lignes[0].estime_j).toBe(20);
  });

  it("lit aussi un fichier séparé par des virgules", () => {
    const lignes = parseProjectsCsv("label,estime_j\nPortail,20");

    expect(lignes[0].label).toBe("Portail");
    expect(lignes[0].estime_j).toBe(20);
  });

  it("se moque de l'ordre des colonnes", () => {
    const lignes = parseProjectsCsv("estime_j;label\n30;Extranet");

    expect(lignes[0].label).toBe("Extranet");
    expect(lignes[0].estime_j).toBe(30);
  });

  it("ignore les colonnes qu'il ne connaît pas", () => {
    const lignes = parseProjectsCsv("label;Service / BU;estime_j\nPortail;DSI;20");

    expect(lignes[0].label).toBe("Portail");
    expect(lignes[0].estime_j).toBe(20);
  });

  it("accepte une virgule décimale", () => {
    expect(parseProjectsCsv("label;estime_j\nPortail;7,5")[0].estime_j).toBe(7.5);
  });

  it("laisse l'estimé vide plutôt que d'inventer un zéro", () => {
    expect(parseProjectsCsv("label;estime_j\nPortail;")[0].estime_j).toBeNull();
  });

  it("rattache un lot à son projet par le libellé", () => {
    const lignes = parseProjectsCsv("label;kind;parent_label\nLot API;lot;Portail");

    expect(lignes[0].kind).toBe("lot");
    expect(lignes[0].parent_label).toBe("Portail");
  });

  it("considère une mission comme un projet par défaut", () => {
    expect(parseProjectsCsv("label\nPortail")[0].kind).toBe("projet");
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

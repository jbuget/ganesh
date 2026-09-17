import { describe, expect, it } from "vitest";

import type { ProjectListItemResponse } from "@/lib/api/generated/model";
import {
  AUCUN_TRI,
  comparateurDeTri,
  ecrireTri,
  lireTri,
  triSuivant,
  type TriMissions,
} from "@/lib/mission-sort";

const mission = (
  label: string,
  champs: Partial<ProjectListItemResponse["project"]> = {},
  realise = 0,
): ProjectListItemResponse =>
  ({
    project: {
      id: label.length,
      label,
      kind: "projet",
      statut: "exploration",
      priorite: null,
      categorie: null,
      estime_j: null,
      ...champs,
    },
    referents: [],
    intervenants: [],
    realise_j: realise,
    commentaires: 0,
    derniere_maj: null,
  }) as ProjectListItemResponse;

const labels = (missions: ProjectListItemResponse[], tri: TriMissions) =>
  [...missions].sort(comparateurDeTri(tri)).map((m) => m.project.label);

describe("l'ordre du référentiel", () => {
  it("range par phase puis par nom quand aucune colonne n'est demandée", () => {
    const missions = [
      mission("Zèbre", { statut: "exploration" }),
      mission("Alpha", { statut: "exploitation" }),
      mission("Bravo", { statut: "exploration" }),
    ];

    expect(labels(missions, AUCUN_TRI)).toEqual(["Bravo", "Zèbre", "Alpha"]);
  });

  it("range par nom, accents compris", () => {
    const missions = [mission("Zèbre"), mission("Éclair"), mission("Alpha")];

    expect(labels(missions, { colonne: "projet", sens: "asc" })).toEqual([
      "Alpha",
      "Éclair",
      "Zèbre",
    ]);
  });

  it("renverse l'ordre en sens descendant", () => {
    const missions = [mission("Alpha"), mission("Zèbre")];

    expect(labels(missions, { colonne: "projet", sens: "desc" })).toEqual([
      "Zèbre",
      "Alpha",
    ]);
  });

  it("range les phases dans leur ordre de vie, pas dans l'alphabet", () => {
    const missions = [
      mission("Zèbre", { statut: "exploitation" }),
      mission("Alpha", { statut: "cadrage" }),
      mission("Bravo", { statut: "exploration" }),
    ];

    expect(labels(missions, { colonne: "phase", sens: "asc" })).toEqual([
      "Bravo",
      "Alpha",
      "Zèbre",
    ]);
  });

  it("range les priorités de la plus forte à la plus faible", () => {
    const missions = [
      mission("Basse", { priorite: "basse" }),
      mission("Critique", { priorite: "critique" }),
      mission("Normale", { priorite: "normale" }),
    ];

    expect(labels(missions, { colonne: "priorite", sens: "asc" })).toEqual([
      "Critique",
      "Normale",
      "Basse",
    ]);
  });

  it("range les estimés par valeur, et non par leur écriture", () => {
    const missions = [
      mission("Neuf", { estime_j: 9 }),
      mission("Dix", { estime_j: 10 }),
    ];

    expect(labels(missions, { colonne: "estime", sens: "asc" })).toEqual([
      "Neuf",
      "Dix",
    ]);
  });

  it("range les réalisés par valeur", () => {
    const missions = [mission("Beaucoup", {}, 12), mission("Peu", {}, 3)];

    expect(labels(missions, { colonne: "realise", sens: "asc" })).toEqual([
      "Peu",
      "Beaucoup",
    ]);
  });

  it("laisse les valeurs manquantes en fin de liste, dans les deux sens", () => {
    // Un estime absent n'est pas un petit estime : il n'a rien a dire, et ne
    // doit pas occuper la tete du tableau quand on cherche les gros chantiers.
    const missions = [
      mission("Sans", { estime_j: null }),
      mission("Avec", { estime_j: 5 }),
    ];

    expect(labels(missions, { colonne: "estime", sens: "asc" })).toEqual([
      "Avec",
      "Sans",
    ]);
    expect(labels(missions, { colonne: "estime", sens: "desc" })).toEqual([
      "Avec",
      "Sans",
    ]);
  });

  it("départage par le nom deux missions que la colonne égalise", () => {
    const missions = [
      mission("Zèbre", { estime_j: 5 }),
      mission("Alpha", { estime_j: 5 }),
    ];

    expect(labels(missions, { colonne: "estime", sens: "asc" })).toEqual([
      "Alpha",
      "Zèbre",
    ]);
  });
});

describe("le cycle d'une colonne", () => {
  it("part en ordre croissant au premier clic", () => {
    expect(triSuivant(AUCUN_TRI, "estime")).toEqual({ colonne: "estime", sens: "asc" });
  });

  it("passe en décroissant au deuxième", () => {
    expect(triSuivant({ colonne: "estime", sens: "asc" }, "estime")).toEqual({
      colonne: "estime",
      sens: "desc",
    });
  });

  it("revient à l'ordre du référentiel au troisième", () => {
    expect(triSuivant({ colonne: "estime", sens: "desc" }, "estime")).toEqual(
      AUCUN_TRI,
    );
  });

  it("repart en croissant quand on change de colonne", () => {
    expect(triSuivant({ colonne: "estime", sens: "desc" }, "phase")).toEqual({
      colonne: "phase",
      sens: "asc",
    });
  });
});

describe("le tri dans l'adresse", () => {
  it("ne lit aucun tri dans une adresse nue", () => {
    expect(lireTri(new URLSearchParams())).toEqual(AUCUN_TRI);
  });

  it("relit le tri qu'il a écrit", () => {
    const params = new URLSearchParams();
    ecrireTri(params, { colonne: "priorite", sens: "desc" });

    expect(lireTri(params)).toEqual({ colonne: "priorite", sens: "desc" });
  });

  it("efface le tri de l'adresse quand on revient à l'ordre par défaut", () => {
    const params = new URLSearchParams("tri=phase&sens=desc");
    ecrireTri(params, AUCUN_TRI);

    expect(params.toString()).toBe("");
  });

  it("ignore une colonne inconnue plutôt que de trier au hasard", () => {
    expect(lireTri(new URLSearchParams("tri=licorne&sens=asc"))).toEqual(AUCUN_TRI);
  });

  it("retient l'ordre croissant quand le sens est illisible", () => {
    expect(lireTri(new URLSearchParams("tri=phase&sens=lateral"))).toEqual({
      colonne: "phase",
      sens: "asc",
    });
  });

  it("laisse les autres paramètres de l'adresse en place", () => {
    const params = new URLSearchParams("phase=cadrage");
    ecrireTri(params, { colonne: "projet", sens: "asc" });

    expect(params.get("phase")).toBe("cadrage");
  });
});

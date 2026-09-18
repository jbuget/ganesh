import { describe, expect, it } from "vitest";

import type { ProjectListItemResponse } from "@/lib/api/generated/model";
import {
  NO_SORT,
  comparateurDeTri,
  writeSort,
  readSort,
  triSuivant,
  type MissionSort,
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
      kind: "project",
      status: "exploration",
      priority: null,
      category: null,
      estimated_days: null,
      ...champs,
    },
    leads: [],
    contributors: [],
    delivered_days: realise,
    comments: 0,
    latest_update: null,
  }) as ProjectListItemResponse;

const labels = (missions: ProjectListItemResponse[], sorted: MissionSort) =>
  [...missions].sort(comparateurDeTri(sorted)).map((m) => m.project.label);

describe("l'ordre du référentiel", () => {
  it("range par phase puis par nom quand aucune colonne n'est demandée", () => {
    const missions = [
      mission("Zèbre", { status: "exploration" }),
      mission("Alpha", { status: "operations" }),
      mission("Bravo", { status: "exploration" }),
    ];

    expect(labels(missions, NO_SORT)).toEqual(["Bravo", "Zèbre", "Alpha"]);
  });

  it("range par nom, accents compris", () => {
    const missions = [mission("Zèbre"), mission("Éclair"), mission("Alpha")];

    expect(labels(missions, { column: "project", direction: "asc" })).toEqual([
      "Alpha",
      "Éclair",
      "Zèbre",
    ]);
  });

  it("renverse l'ordre en sens descendant", () => {
    const missions = [mission("Alpha"), mission("Zèbre")];

    expect(labels(missions, { column: "project", direction: "desc" })).toEqual([
      "Zèbre",
      "Alpha",
    ]);
  });

  it("range les phases dans leur ordre de vie, pas dans l'alphabet", () => {
    const missions = [
      mission("Zèbre", { status: "operations" }),
      mission("Alpha", { status: "scoping" }),
      mission("Bravo", { status: "exploration" }),
    ];

    expect(labels(missions, { column: "phase", direction: "asc" })).toEqual([
      "Bravo",
      "Alpha",
      "Zèbre",
    ]);
  });

  it("range les priorités de la plus forte à la plus faible", () => {
    const missions = [
      mission("Basse", { priority: "low" }),
      mission("Critique", { priority: "critical" }),
      mission("Normale", { priority: "normal" }),
    ];

    expect(labels(missions, { column: "priority", direction: "asc" })).toEqual([
      "Critique",
      "Normale",
      "Basse",
    ]);
  });

  it("range les estimés par valeur, et non par leur écriture", () => {
    const missions = [
      mission("Neuf", { estimated_days: 9 }),
      mission("Dix", { estimated_days: 10 }),
    ];

    expect(labels(missions, { column: "estimated", direction: "asc" })).toEqual([
      "Neuf",
      "Dix",
    ]);
  });

  it("range les réalisés par valeur", () => {
    const missions = [mission("Beaucoup", {}, 12), mission("Peu", {}, 3)];

    expect(labels(missions, { column: "delivered", direction: "asc" })).toEqual([
      "Peu",
      "Beaucoup",
    ]);
  });

  it("laisse les valeurs manquantes en fin de liste, dans les deux sens", () => {
    // A missing estimate is not a small estimate: it has nothing to say, and
    // must not sit at the top when one is looking for the big jobs.
    const missions = [
      mission("Sans", { estimated_days: null }),
      mission("Avec", { estimated_days: 5 }),
    ];

    expect(labels(missions, { column: "estimated", direction: "asc" })).toEqual([
      "Avec",
      "Sans",
    ]);
    expect(labels(missions, { column: "estimated", direction: "desc" })).toEqual([
      "Avec",
      "Sans",
    ]);
  });

  it("départage par le nom deux missions que la colonne égalise", () => {
    const missions = [
      mission("Zèbre", { estimated_days: 5 }),
      mission("Alpha", { estimated_days: 5 }),
    ];

    expect(labels(missions, { column: "estimated", direction: "asc" })).toEqual([
      "Alpha",
      "Zèbre",
    ]);
  });
});

describe("le cycle d'une colonne", () => {
  it("part en ordre croissant au premier clic", () => {
    expect(triSuivant(NO_SORT, "estimated")).toEqual({
      column: "estimated",
      direction: "asc",
    });
  });

  it("passe en décroissant au deuxième", () => {
    expect(triSuivant({ column: "estimated", direction: "asc" }, "estimated")).toEqual({
      column: "estimated",
      direction: "desc",
    });
  });

  it("revient à l'ordre du référentiel au troisième", () => {
    expect(triSuivant({ column: "estimated", direction: "desc" }, "estimated")).toEqual(
      NO_SORT,
    );
  });

  it("repart en croissant quand on change de colonne", () => {
    expect(triSuivant({ column: "estimated", direction: "desc" }, "phase")).toEqual({
      column: "phase",
      direction: "asc",
    });
  });
});

describe("le tri dans l'adresse", () => {
  it("ne lit aucun tri dans une adresse nue", () => {
    expect(readSort(new URLSearchParams())).toEqual(NO_SORT);
  });

  it("relit le tri qu'il a écrit", () => {
    const params = new URLSearchParams();
    writeSort(params, { column: "priority", direction: "desc" });

    expect(readSort(params)).toEqual({ column: "priority", direction: "desc" });
  });

  it("efface le tri de l'adresse quand on revient à l'ordre par défaut", () => {
    const params = new URLSearchParams("sort=phase&direction=desc");
    writeSort(params, NO_SORT);

    expect(params.toString()).toBe("");
  });

  it("ignore une colonne inconnue plutôt que de trier au hasard", () => {
    expect(readSort(new URLSearchParams("sort=licorne&direction=asc"))).toEqual(
      NO_SORT,
    );
  });

  it("retient l'ordre croissant quand le sens est illisible", () => {
    expect(readSort(new URLSearchParams("sort=phase&direction=lateral"))).toEqual({
      column: "phase",
      direction: "asc",
    });
  });

  it("laisse les autres paramètres de l'adresse en place", () => {
    const params = new URLSearchParams("phase=scoping");
    writeSort(params, { column: "project", direction: "asc" });

    expect(params.get("phase")).toBe("scoping");
  });
});

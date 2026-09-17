import { describe, expect, it } from "vitest";

import { buildProjectTree, offProjectActivities } from "./project-tree";
import type { ProjectListItemResponse } from "@/lib/api/generated/model";

const mission = (
  id: number,
  label: string,
  kind: string,
  parent_id: number | null = null,
  statut: string | null = null,
): ProjectListItemResponse =>
  ({
    project: {
      id,
      label,
      kind,
      parent_id,
      statut,
      actif: true,
      estime_j: null,
      is_syncable_to_monday: false,
    },
    referents: [],
    intervenants: [],
  }) as unknown as ProjectListItemResponse;

describe("buildProjectTree", () => {
  it("rattache chaque lot à son projet", () => {
    const arbre = buildProjectTree([
      mission(1, "Portail", "projet"),
      mission(2, "Lot API", "lot", 1),
      mission(3, "Lot Front", "lot", 1),
    ]);

    expect(arbre).toHaveLength(1);
    expect(arbre[0].lots.map((l) => l.project.label)).toEqual(["Lot API", "Lot Front"]);
  });

  it("classe les projets et les lots par ordre alphabétique", () => {
    const arbre = buildProjectTree([
      mission(1, "Zeta", "projet"),
      mission(2, "Alpha", "projet"),
    ]);

    expect(arbre.map((n) => n.mission.project.label)).toEqual(["Alpha", "Zeta"]);
  });

  it("range les projets par phase, dans l'ordre des colonnes du kanban", () => {
    const arbre = buildProjectTree([
      mission(1, "Alpha", "projet", null, "exploitation"),
      mission(2, "Beta", "projet", null, "exploration"),
      mission(3, "Gamma", "projet", null, "realisation"),
    ]);

    expect(arbre.map((n) => n.mission.project.label)).toEqual([
      "Beta",
      "Gamma",
      "Alpha",
    ]);
  });

  it("classe par ordre alphabétique à phase égale", () => {
    const arbre = buildProjectTree([
      mission(1, "Zeta", "projet", null, "cadrage"),
      mission(2, "Alpha", "projet", null, "cadrage"),
    ]);

    expect(arbre.map((n) => n.mission.project.label)).toEqual(["Alpha", "Zeta"]);
  });

  it("range de même les lots sous leur projet", () => {
    const arbre = buildProjectTree([
      mission(1, "Portail", "projet", null, "cadrage"),
      mission(2, "Lot livré", "lot", 1, "exploitation"),
      mission(3, "Lot en cours", "lot", 1, "realisation"),
    ]);

    expect(arbre[0].lots.map((l) => l.project.label)).toEqual([
      "Lot en cours",
      "Lot livré",
    ]);
  });

  it("remonte un lot dont le parent est absent plutôt que de le perdre", () => {
    const arbre = buildProjectTree([
      mission(1, "Portail", "projet"),
      mission(9, "Lot orphelin", "lot", 404),
    ]);

    expect(arbre.map((n) => n.mission.project.label)).toEqual([
      "Portail",
      "Lot orphelin",
    ]);
  });

  it("remonte aussi un lot sans parent déclaré", () => {
    const arbre = buildProjectTree([mission(9, "Lot seul", "lot", null)]);

    expect(arbre.map((n) => n.mission.project.label)).toEqual(["Lot seul"]);
  });

  it("écarte les activités hors projet de l'arborescence", () => {
    const arbre = buildProjectTree([
      mission(1, "Portail", "projet"),
      mission(2, "Absences", "hors_projet"),
    ]);

    expect(arbre.map((n) => n.mission.project.label)).toEqual(["Portail"]);
  });

  it("ne perd aucun projet quand il n'y a aucun lot", () => {
    const arbre = buildProjectTree([mission(1, "Portail", "projet")]);

    expect(arbre[0].lots).toEqual([]);
  });
});

describe("offProjectActivities", () => {
  it("ne retient que les activités hors projet, triées", () => {
    const activites = offProjectActivities([
      mission(1, "Portail", "projet"),
      mission(3, "Formation", "hors_projet"),
      mission(2, "Absences", "hors_projet"),
    ]);

    expect(activites.map((a) => a.project.label)).toEqual(["Absences", "Formation"]);
  });
});

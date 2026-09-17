import { describe, expect, it } from "vitest";

import { buildProjectTree, offProjectActivities } from "./project-tree";
import type { ProjectResponse } from "@/lib/api/generated/model";

const mission = (
  id: number,
  label: string,
  kind: string,
  parent_id: number | null = null,
): ProjectResponse =>
  ({
    id,
    label,
    kind,
    parent_id,
    statut: null,
    actif: true,
    estime_j: null,
    is_syncable_to_monday: false,
  }) as ProjectResponse;

describe("buildProjectTree", () => {
  it("rattache chaque lot à son projet", () => {
    const arbre = buildProjectTree([
      mission(1, "Portail", "projet"),
      mission(2, "Lot API", "lot", 1),
      mission(3, "Lot Front", "lot", 1),
    ]);

    expect(arbre).toHaveLength(1);
    expect(arbre[0].lots.map((l) => l.label)).toEqual(["Lot API", "Lot Front"]);
  });

  it("classe les projets et les lots par ordre alphabétique", () => {
    const arbre = buildProjectTree([
      mission(1, "Zeta", "projet"),
      mission(2, "Alpha", "projet"),
    ]);

    expect(arbre.map((n) => n.project.label)).toEqual(["Alpha", "Zeta"]);
  });

  it("remonte un lot dont le parent est absent plutôt que de le perdre", () => {
    const arbre = buildProjectTree([
      mission(1, "Portail", "projet"),
      mission(9, "Lot orphelin", "lot", 404),
    ]);

    expect(arbre.map((n) => n.project.label)).toEqual(["Portail", "Lot orphelin"]);
  });

  it("remonte aussi un lot sans parent déclaré", () => {
    const arbre = buildProjectTree([mission(9, "Lot seul", "lot", null)]);

    expect(arbre.map((n) => n.project.label)).toEqual(["Lot seul"]);
  });

  it("écarte les activités hors projet de l'arborescence", () => {
    const arbre = buildProjectTree([
      mission(1, "Portail", "projet"),
      mission(2, "Absences", "hors_projet"),
    ]);

    expect(arbre.map((n) => n.project.label)).toEqual(["Portail"]);
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

    expect(activites.map((a) => a.label)).toEqual(["Absences", "Formation"]);
  });
});

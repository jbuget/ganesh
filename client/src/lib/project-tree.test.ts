import { describe, expect, it } from "vitest";

import { buildProjectTree, offProjectActivities } from "./project-tree";
import type { ProjectListItemResponse } from "@/lib/api/generated/model";

const mission = (
  id: number,
  label: string,
  kind: string,
  parent_id: number | null = null,
  status: string | null = null,
): ProjectListItemResponse =>
  ({
    project: {
      id,
      label,
      kind,
      parent_id,
      status,
      is_active: true,
      estimated_days: null,
      is_syncable_to_monday: false,
    },
    leads: [],
    contributors: [],
  }) as unknown as ProjectListItemResponse;

describe("buildProjectTree", () => {
  it("rattache chaque lot à son projet", () => {
    const tree = buildProjectTree([
      mission(1, "Portail", "project"),
      mission(2, "Lot API", "work_package", 1),
      mission(3, "Lot Front", "work_package", 1),
    ]);

    expect(tree).toHaveLength(1);
    expect(tree[0].lots.map((l) => l.project.label)).toEqual(["Lot API", "Lot Front"]);
  });

  it("classe les projets et les lots par ordre alphabétique", () => {
    const tree = buildProjectTree([
      mission(1, "Zeta", "project"),
      mission(2, "Alpha", "project"),
    ]);

    expect(tree.map((n) => n.mission.project.label)).toEqual(["Alpha", "Zeta"]);
  });

  it("range les projets par phase, dans l'ordre des colonnes du kanban", () => {
    const tree = buildProjectTree([
      mission(1, "Alpha", "project", null, "operations"),
      mission(2, "Beta", "project", null, "exploration"),
      mission(3, "Gamma", "project", null, "build"),
    ]);

    expect(tree.map((n) => n.mission.project.label)).toEqual([
      "Beta",
      "Gamma",
      "Alpha",
    ]);
  });

  it("classe par ordre alphabétique à phase égale", () => {
    const tree = buildProjectTree([
      mission(1, "Zeta", "project", null, "scoping"),
      mission(2, "Alpha", "project", null, "scoping"),
    ]);

    expect(tree.map((n) => n.mission.project.label)).toEqual(["Alpha", "Zeta"]);
  });

  it("range de même les lots sous leur projet", () => {
    const tree = buildProjectTree([
      mission(1, "Portail", "project", null, "scoping"),
      mission(2, "Lot livré", "work_package", 1, "operations"),
      mission(3, "Lot en cours", "work_package", 1, "build"),
    ]);

    expect(tree[0].lots.map((l) => l.project.label)).toEqual([
      "Lot en cours",
      "Lot livré",
    ]);
  });

  it("remonte un lot dont le parent est absent plutôt que de le perdre", () => {
    const tree = buildProjectTree([
      mission(1, "Portail", "project"),
      mission(9, "Lot orphelin", "work_package", 404),
    ]);

    expect(tree.map((n) => n.mission.project.label)).toEqual([
      "Portail",
      "Lot orphelin",
    ]);
  });

  it("remonte aussi un lot sans parent déclaré", () => {
    const tree = buildProjectTree([mission(9, "Lot seul", "work_package", null)]);

    expect(tree.map((n) => n.mission.project.label)).toEqual(["Lot seul"]);
  });

  it("écarte les activités hors projet de l'arborescence", () => {
    const tree = buildProjectTree([
      mission(1, "Portail", "project"),
      mission(2, "Absences", "off_project"),
    ]);

    expect(tree.map((n) => n.mission.project.label)).toEqual(["Portail"]);
  });

  it("ne perd aucun projet quand il n'y a aucun lot", () => {
    const tree = buildProjectTree([mission(1, "Portail", "project")]);

    expect(tree[0].lots).toEqual([]);
  });
});

describe("offProjectActivities", () => {
  it("ne retient que les activités hors projet, triées", () => {
    const activities = offProjectActivities([
      mission(1, "Portail", "project"),
      mission(3, "Formation", "off_project"),
      mission(2, "Absences", "off_project"),
    ]);

    expect(activities.map((a) => a.project.label)).toEqual(["Absences", "Formation"]);
  });
});

describe("buildProjectTree, rangé sur une colonne", () => {
  it("applique le tri aux projets", () => {
    const tree = buildProjectTree(
      [
        mission(1, "Alpha", "project", null, "exploration"),
        mission(2, "Bravo", "project", null, "exploration"),
      ],
      { column: "project", direction: "desc" },
    );

    expect(tree.map((n) => n.mission.project.label)).toEqual(["Bravo", "Alpha"]);
  });

  it("garde chaque lot sous son projet", () => {
    // Trier ne doit jamais remonter un sous-projet au premier niveau : la
    // liste se range, l'arborescence ne bouge pas.
    const tree = buildProjectTree(
      [
        mission(1, "Alpha", "project"),
        mission(2, "Zoulou", "work_package", 1),
        mission(3, "Delta", "work_package", 1),
      ],
      { column: "project", direction: "desc" },
    );

    expect(tree).toHaveLength(1);
    expect(tree[0].lots.map((l) => l.project.label)).toEqual(["Zoulou", "Delta"]);
  });
});

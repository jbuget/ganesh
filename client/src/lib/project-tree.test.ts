import { describe, expect, it } from "vitest";

import { buildProjectTree } from "./project-tree";
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
  it("attaches each work package to its project", () => {
    const tree = buildProjectTree([
      mission(1, "Portail", "project"),
      mission(2, "Lot API", "work_package", 1),
      mission(3, "Lot Front", "work_package", 1),
    ]);

    expect(tree).toHaveLength(1);
    expect(tree[0].workPackages.map((l) => l.project.label)).toEqual([
      "Lot API",
      "Lot Front",
    ]);
  });

  it("ranks projects and work packages alphabetically", () => {
    const tree = buildProjectTree([
      mission(1, "Zeta", "project"),
      mission(2, "Alpha", "project"),
    ]);

    expect(tree.map((n) => n.mission.project.label)).toEqual(["Alpha", "Zeta"]);
  });

  it("arranges projects by phase, in kanban column order", () => {
    const tree = buildProjectTree([
      mission(1, "Alpha", "project", null, "operations"),
      mission(2, "Beta", "project", null, "exploration"),
      mission(3, "Gamma", "project", null, "development"),
    ]);

    expect(tree.map((n) => n.mission.project.label)).toEqual([
      "Beta",
      "Gamma",
      "Alpha",
    ]);
  });

  it("ranks alphabetically at equal phase", () => {
    const tree = buildProjectTree([
      mission(1, "Zeta", "project", null, "scoping"),
      mission(2, "Alpha", "project", null, "scoping"),
    ]);

    expect(tree.map((n) => n.mission.project.label)).toEqual(["Alpha", "Zeta"]);
  });

  it("arranges the work packages under their project the same way", () => {
    const tree = buildProjectTree([
      mission(1, "Portail", "project", null, "scoping"),
      mission(2, "Lot livré", "work_package", 1, "operations"),
      mission(3, "Lot en cours", "work_package", 1, "development"),
    ]);

    expect(tree[0].workPackages.map((l) => l.project.label)).toEqual([
      "Lot en cours",
      "Lot livré",
    ]);
  });

  it("lifts a work package whose parent is missing rather than losing it", () => {
    const tree = buildProjectTree([
      mission(1, "Portail", "project"),
      mission(9, "Lot orphelin", "work_package", 404),
    ]);

    expect(tree.map((n) => n.mission.project.label)).toEqual([
      "Portail",
      "Lot orphelin",
    ]);
  });

  it("also lifts a work package with no declared parent", () => {
    const tree = buildProjectTree([mission(9, "Lot seul", "work_package", null)]);

    expect(tree.map((n) => n.mission.project.label)).toEqual(["Lot seul"]);
  });

  it("keeps off-project work out of the tree", () => {
    const tree = buildProjectTree([
      mission(1, "Portail", "project"),
      mission(2, "Absences", "off_project"),
    ]);

    expect(tree.map((n) => n.mission.project.label)).toEqual(["Portail"]);
  });

  it("loses no project when there is no work package", () => {
    const tree = buildProjectTree([mission(1, "Portail", "project")]);

    expect(tree[0].workPackages).toEqual([]);
  });
});

describe("buildProjectTree, arranged on a column", () => {
  it("applies the sort to the projects", () => {
    const tree = buildProjectTree(
      [
        mission(1, "Alpha", "project", null, "exploration"),
        mission(2, "Bravo", "project", null, "exploration"),
      ],
      { column: "project", direction: "desc" },
    );

    expect(tree.map((n) => n.mission.project.label)).toEqual(["Bravo", "Alpha"]);
  });

  it("keeps each work package under its project", () => {
    // Sorting must never lift a sub-project to the first level: the list gets
    // ordered, the tree does not move.
    const tree = buildProjectTree(
      [
        mission(1, "Alpha", "project"),
        mission(2, "Zoulou", "work_package", 1),
        mission(3, "Delta", "work_package", 1),
      ],
      { column: "project", direction: "desc" },
    );

    expect(tree).toHaveLength(1);
    expect(tree[0].workPackages.map((l) => l.project.label)).toEqual([
      "Zoulou",
      "Delta",
    ]);
  });
});

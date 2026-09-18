import { describe, expect, it } from "vitest";

import { availableMissions } from "./missions";
import type { ProjectResponse } from "@/lib/api/generated/model";

const project = (id: number, label: string, kind: string): ProjectResponse =>
  ({
    id,
    label,
    kind,
    status: null,
    parent_id: null,
    is_active: true,
    estimated_days: null,
    is_syncable_to_monday: false,
  }) as ProjectResponse;

const PROJECTS = [
  project(1, "Portail bailleurs", "project"),
  project(2, "Absences", "off_project"),
  project(3, "Lot 1", "work_package"),
];

describe("availableMissions", () => {
  it("separates projects and work packages from off-project work", () => {
    const { projets, horsProjet } = availableMissions(PROJECTS, []);

    expect(projets.map((p) => p.label)).toEqual(["Portail bailleurs", "Lot 1"]);
    expect(horsProjet.map((p) => p.label)).toEqual(["Absences"]);
  });

  it("rules out missions already in the grid", () => {
    const { projets } = availableMissions(PROJECTS, [1]);

    expect(projets.map((p) => p.label)).toEqual(["Lot 1"]);
  });

  it("may have nothing left to offer", () => {
    const { projets, horsProjet } = availableMissions(PROJECTS, [1, 2, 3]);

    expect(projets).toEqual([]);
    expect(horsProjet).toEqual([]);
  });

  it("does not change the list received", () => {
    const copie = [...PROJECTS];
    availableMissions(PROJECTS, [1]);

    expect(PROJECTS).toEqual(copie);
  });
});

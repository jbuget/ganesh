import { describe, expect, it } from "vitest";

import { availableMissions } from "./missions";
import type { ProjectResponse } from "@/lib/api/generated/model";

const project = (id: number, label: string, kind: string): ProjectResponse =>
  ({
    id,
    label,
    kind,
    statut: null,
    parent_id: null,
    actif: true,
    estime_j: null,
    is_syncable_to_monday: false,
  }) as ProjectResponse;

const PROJECTS = [
  project(1, "Portail bailleurs", "projet"),
  project(2, "Absences", "hors_projet"),
  project(3, "Lot 1", "lot"),
];

describe("availableMissions", () => {
  it("sépare les projets et les lots des activités hors projet", () => {
    const { projets, horsProjet } = availableMissions(PROJECTS, []);

    expect(projets.map((p) => p.label)).toEqual(["Portail bailleurs", "Lot 1"]);
    expect(horsProjet.map((p) => p.label)).toEqual(["Absences"]);
  });

  it("écarte les missions déjà présentes dans la matrice", () => {
    const { projets } = availableMissions(PROJECTS, [1]);

    expect(projets.map((p) => p.label)).toEqual(["Lot 1"]);
  });

  it("peut ne plus rien avoir à proposer", () => {
    const { projets, horsProjet } = availableMissions(PROJECTS, [1, 2, 3]);

    expect(projets).toEqual([]);
    expect(horsProjet).toEqual([]);
  });

  it("ne modifie pas la liste reçue", () => {
    const copie = [...PROJECTS];
    availableMissions(PROJECTS, [1]);

    expect(PROJECTS).toEqual(copie);
  });
});

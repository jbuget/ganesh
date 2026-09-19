import { describe, expect, it } from "vitest";

import type { ProjectResponse } from "@/lib/api/generated/model";
import { publicationBlockers, suggestSlug } from "@/lib/service-sheet";

const project = (overrides: Partial<ProjectResponse> = {}) =>
  ({
    id: 1,
    label: "Portail bailleurs",
    kind: "project",
    slug: null,
    summary: null,
    ...overrides,
  }) as unknown as ProjectResponse;

describe("suggestSlug", () => {
  it("turns a label into an address", () => {
    expect(suggestSlug("Portail bailleurs")).toBe("portail-bailleurs");
  });

  it("drops the accents rather than escaping them", () => {
    expect(suggestSlug("Réception des PV")).toBe("reception-des-pv");
  });

  it("collapses what is neither a letter nor a digit", () => {
    expect(suggestSlug("Monta — Toolbox (v2)")).toBe("monta-toolbox-v2");
  });

  it("never starts or ends on a hyphen", () => {
    expect(suggestSlug("  !! ASTRE !!  ")).toBe("astre");
  });

  it("returns nothing when the label carries no letter", () => {
    expect(suggestSlug("!!!")).toBe("");
  });
});

describe("publicationBlockers", () => {
  it("names the address and the summary while both are missing", () => {
    expect(publicationBlockers(project())).toEqual(["l'adresse publique", "le résumé"]);
  });

  it("names only what is still missing", () => {
    expect(publicationBlockers(project({ slug: "portail" }))).toEqual(["le résumé"]);
  });

  it("finds nothing in the way of a complete sheet", () => {
    expect(
      publicationBlockers(project({ slug: "portail", summary: "Un portail." })),
    ).toEqual([]);
  });

  it("turns off-project work away whatever it carries", () => {
    const absences = project({
      kind: "off_project",
      slug: "conges",
      summary: "Absences.",
    });
    expect(publicationBlockers(absences)).toEqual([
      "une activité hors projet ne se publie pas",
    ]);
  });
});

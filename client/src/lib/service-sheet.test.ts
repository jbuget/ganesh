import { describe, expect, it } from "vitest";

import type { ProjectResponse } from "@/lib/api/generated/model";
import {
  frenchList,
  publicationBlockers,
  slugError,
  suggestSlug,
} from "@/lib/service-sheet";

const project = (overrides: Partial<ProjectResponse> = {}) =>
  ({
    id: 1,
    label: "Portail bailleurs",
    kind: "project",
    slug: null,
    summary: null,
    criticality: null,
    service_type: null,
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
  it("names everything missing at once", () => {
    expect(publicationBlockers(project())).toEqual([
      "le slug",
      "le résumé",
      "la criticité",
      "le type",
    ]);
  });

  it("names only what is still missing", () => {
    const half = project({ slug: "portail", criticality: "standard" });
    expect(publicationBlockers(half)).toEqual(["le résumé", "le type"]);
  });

  it("finds nothing in the way of a complete sheet", () => {
    const complete = project({
      slug: "portail",
      summary: "Un portail.",
      criticality: "standard",
      service_type: "fullstack",
    });
    expect(publicationBlockers(complete)).toEqual([]);
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

describe("frenchList", () => {
  it("says nothing of an empty list", () => {
    expect(frenchList([])).toBe("");
  });

  it("leaves a single item alone", () => {
    expect(frenchList(["le résumé"])).toBe("le résumé");
  });

  it("joins two items with et", () => {
    expect(frenchList(["le résumé", "le type"])).toBe("le résumé et le type");
  });

  it("lets the comma do the work and keeps et for the last", () => {
    expect(frenchList(["a", "b", "c"])).toBe("a, b et c");
  });
});

describe("slugError", () => {
  it("accepts a slug written as the catalogue reads it", () => {
    expect(slugError("portail-bailleurs")).toBeNull();
  });

  it("accepts an emptied field: not every mission is published", () => {
    expect(slugError(null)).toBeNull();
  });

  it("refuses a whole URL, which is what one is tempted to paste", () => {
    expect(slugError("https://lorem-ipsum.waat.tools")).toBe(
      "Un slug s'écrit en minuscules, chiffres et tirets — « portail-bailleurs », pas une URL entière.",
    );
  });

  it("refuses capitals and spaces", () => {
    expect(slugError("Portail Bailleurs")).not.toBeNull();
  });

  it("refuses a slug longer than the column holds", () => {
    expect(slugError("a".repeat(101))).toBe("Un slug ne dépasse pas 100 caractères.");
  });
});

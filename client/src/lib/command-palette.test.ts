import { describe, expect, it } from "vitest";

import { destinations, grouped, matching } from "./command-palette";
import type { ProjectListItemResponse, UserResponse } from "@/lib/api/generated/model";

const mission = (over: Record<string, unknown> = {}): ProjectListItemResponse =>
  ({
    leads: [],
    contributors: [],
    delivered_days: 0,
    links: [],
    departments: [],
    comments: 0,
    latest_update: null,
    project: {
      id: 1,
      label: "Portail bailleurs",
      kind: "project",
      status: "development",
      parent_id: null,
      is_active: true,
      archived_at: null,
      ...over,
    },
  }) as unknown as ProjectListItemResponse;

const teammate = (over: Record<string, unknown> = {}): UserResponse =>
  ({
    id: 7,
    email: "lea.chen@waat.fr",
    display_name: "Léa Chen",
    initials: "LC",
    role: "TEAMMATE",
    is_active: true,
    ...over,
  }) as UserResponse;

const labelsOf = (found: { label: string }[]) => found.map((one) => one.label);

describe("destinations", () => {
  it("leads to every screen of the application", () => {
    const all = destinations({ missions: [], teammates: [] });
    const screens = all.filter((one) => one.group === "screen");

    expect(labelsOf(screens)).toContain("Saisie des temps");
    expect(screens[0]).toMatchObject({ label: "Accueil", href: "/" });
  });

  it("leads to a project's sheet", () => {
    const all = destinations({ missions: [mission({ id: 12 })], teammates: [] });

    expect(all.find((one) => one.group === "project")).toMatchObject({
      label: "Portail bailleurs",
      href: "/projects/12",
      status: "development",
    });
  });

  it("opens a teammate's panel", () => {
    const all = destinations({ missions: [], teammates: [teammate()] });

    expect(all.find((one) => one.group === "person")).toMatchObject({
      label: "Léa Chen",
      href: "/users?user=7",
      hint: "lea.chen@waat.fr",
    });
  });

  it("says of an archived project that it is archived", () => {
    const all = destinations({
      missions: [mission({ is_active: false, archived_at: "2026-03-02" })],
      teammates: [],
    });

    expect(all.find((one) => one.group === "project")?.hint).toBe("Archivé");
  });

  it("says which project a work package belongs to", () => {
    const all = destinations({
      missions: [
        mission({ id: 1, label: "Portail bailleurs" }),
        mission({
          id: 2,
          label: "Reprise de données",
          kind: "work_package",
          parent_id: 1,
        }),
      ],
      teammates: [],
    });

    expect(all.find((one) => one.label === "Reprise de données")?.hint).toBe(
      "Sous-projet de Portail bailleurs",
    );
  });

  it("says of off-project work that it is off-project", () => {
    const all = destinations({
      missions: [mission({ label: "Congés", kind: "off_project", status: null })],
      teammates: [],
    });

    expect(all.find((one) => one.label === "Congés")?.hint).toBe("Hors-projet");
  });
});

describe("matching", () => {
  const all = destinations({
    missions: [
      mission({ id: 12, label: "Portail bailleurs" }),
      mission({ id: 13, label: "Copropriété connectée" }),
      mission({ id: 14, label: "Refonte du portail" }),
      mission({ id: 15, label: "Support Coach" }),
    ],
    teammates: [teammate()],
  });

  it("shows the screens alone while nothing is typed", () => {
    const found = matching(all, "");

    expect(found.every((one) => one.group === "screen")).toBe(true);
    expect(found).toHaveLength(12);
  });

  it("ignores the case and the accents", () => {
    expect(labelsOf(matching(all, "COPROPRIETE"))).toContain("Copropriété connectée");
    expect(labelsOf(matching(all, "lea"))).toContain("Léa Chen");
  });

  it("reads a teammate's email as well as their name", () => {
    expect(labelsOf(matching(all, "lea.chen@"))).toContain("Léa Chen");
  });

  it("puts what starts with what was typed before what merely carries it", () => {
    const found = matching(all, "port");

    expect(labelsOf(found)).toEqual([
      // The name opens on it, then a word of the name does, then it is only
      // somewhere inside: read in that order, one finds what one aimed at.
      "Portail bailleurs",
      "Refonte du portail",
      "Support Coach",
    ]);
  });

  it("returns nothing when nothing answers", () => {
    expect(matching(all, "zzz")).toEqual([]);
  });

  it("matches on a word within the label", () => {
    expect(labelsOf(matching(all, "temps"))).toContain("Saisie des temps");
  });
});

describe("grouped", () => {
  const all = destinations({
    missions: [mission({ id: 12, label: "Portail bailleurs" })],
    teammates: [teammate({ display_name: "Léa Portal" })],
  });

  it("gathers the results under the heading of their group", () => {
    const sections = grouped(matching(all, "portail"));

    expect(sections).toEqual([
      {
        group: "project",
        label: "Projets",
        items: [expect.objectContaining({ label: "Portail bailleurs" })],
      },
    ]);
  });

  it("puts first the group the best answer is in", () => {
    // « Portail bailleurs » opens on what was typed, « Léa Portal » only has
    // a word that does: the group holding the best answer leads, and the
    // headings do not reorder what the ranking settled.
    const sections = grouped(matching(all, "porta"));

    expect(sections.map((section) => section.group)).toEqual(["project", "person"]);
  });

  it("keeps the order the results came in, within a group", () => {
    const sections = grouped(matching(all, ""));

    expect(sections).toHaveLength(1);
    expect(sections[0].items[0].label).toBe("Accueil");
  });
});

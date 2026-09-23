import { describe, expect, it } from "vitest";

import { destinations, gestureLabel, grouped, matching } from "./command-palette";
import { SCREENS } from "@/lib/navigation";
import type {
  AuditAction,
  ProjectListItemResponse,
  TouchedProjectResponse,
  UserResponse,
} from "@/lib/api/generated/model";

const mission = (
  over: Record<string, unknown> = {},
  updatedAt: string | null = null,
): ProjectListItemResponse =>
  ({
    leads: [],
    contributors: [],
    delivered_days: 0,
    links: [],
    departments: [],
    comments: 0,
    latest_update: updatedAt
      ? {
          author: { id: 1, display_name: "Léa Chen", initials: "LC" },
          body: "…",
          published_at: updatedAt,
        }
      : null,
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
    // Counted from the navigation rather than written down: a screen added
    // reaches the palette by itself, and a count kept here by hand would
    // fail for the one reason that is not a bug.
    expect(found).toHaveLength(SCREENS.length);
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

describe("what has just moved", () => {
  const updated = [
    mission({ id: 1, label: "Portail bailleurs" }, "2026-09-18T09:00:00Z"),
    mission({ id: 2, label: "Extranet syndic" }, "2026-09-20T09:00:00Z"),
    mission({ id: 3, label: "Copropriété connectée" }, "2026-09-19T09:00:00Z"),
  ];

  it("opens on the projects last written about, the freshest first", () => {
    const found = matching(destinations({ missions: updated, teammates: [] }), "");
    const recent = found.filter((one) => one.group === "recent");

    expect(labelsOf(recent)).toEqual([
      "Extranet syndic",
      "Copropriété connectée",
      "Portail bailleurs",
    ]);
    expect(recent[0].at).toBe("2026-09-20T09:00:00Z");
  });

  it("shows them above the screens: one comes to pick up what one left", () => {
    const sections = grouped(
      matching(destinations({ missions: updated, teammates: [] }), ""),
    );

    expect(sections.map((section) => section.label)).toEqual([
      "Activité récente",
      "Écrans",
    ]);
  });

  it("shows five of them at most", () => {
    const many = Array.from({ length: 9 }, (_, rank) =>
      mission(
        { id: rank + 1, label: `Projet ${rank}` },
        `2026-09-0${rank + 1}T09:00:00Z`,
      ),
    );
    const found = matching(destinations({ missions: many, teammates: [] }), "");

    expect(found.filter((one) => one.group === "recent")).toHaveLength(5);
  });

  it("leaves out a project nobody has written about", () => {
    const found = matching(
      destinations({ missions: [mission({ id: 1, label: "Muet" })], teammates: [] }),
      "",
    );

    expect(labelsOf(found)).not.toContain("Muet");
  });

  it("leaves out an archived project: the question is what is moving", () => {
    const found = matching(
      destinations({
        missions: [
          mission(
            { id: 1, label: "Extranet syndic", is_active: false },
            "2026-09-20T09:00:00Z",
          ),
        ],
        teammates: [],
      }),
      "",
    );

    expect(found.every((one) => one.group === "screen")).toBe(true);
  });

  it("names a project once when something is typed, not twice", () => {
    const found = matching(
      destinations({ missions: updated, teammates: [] }),
      "extranet",
    );

    expect(labelsOf(found)).toEqual(["Extranet syndic"]);
    expect(found[0].group).toBe("project");
  });
});

describe("a project that moved without anybody writing about it", () => {
  const silent = mission({ id: 4, label: "Refonte du portail" });
  const moved = (action: string, at: string) =>
    ({ project_id: 4, action, at }) as TouchedProjectResponse;

  it("is offered on the strength of the register alone", () => {
    const found = matching(
      destinations({
        missions: [silent],
        teammates: [],
        touched: [moved("project.status_change", "2026-09-20T09:00:00Z")],
      }),
      "",
    );

    expect(found[0]).toMatchObject({
      label: "Refonte du portail",
      group: "recent",
      gesture: "Phase changée",
      at: "2026-09-20T09:00:00Z",
    });
  });

  it("is announced by whichever of the two happened last", () => {
    const written = mission(
      { id: 4, label: "Refonte du portail" },
      "2026-09-22T09:00:00Z",
    );
    const found = matching(
      destinations({
        missions: [written],
        teammates: [],
        touched: [moved("project.status_change", "2026-09-20T09:00:00Z")],
      }),
      "",
    );

    expect(found[0]).toMatchObject({
      gesture: "Mise à jour",
      at: "2026-09-22T09:00:00Z",
    });
  });

  it("names the older gesture when the update is the older of the two", () => {
    const written = mission(
      { id: 4, label: "Refonte du portail" },
      "2026-09-18T09:00:00Z",
    );
    const found = matching(
      destinations({
        missions: [written],
        teammates: [],
        touched: [moved("attachment.add", "2026-09-20T09:00:00Z")],
      }),
      "",
    );

    expect(found[0]).toMatchObject({ gesture: "Fichier ajouté" });
  });

  it("says nothing of a project the reference list can no longer name", () => {
    const found = matching(
      destinations({
        missions: [],
        teammates: [],
        touched: [moved("project.update", "2026-09-20T09:00:00Z")],
      }),
      "",
    );

    expect(found.every((one) => one.group === "screen")).toBe(true);
  });

  it("says that something happened, for a gesture it has no word for", () => {
    expect(gestureLabel("gazette.generate" as AuditAction)).toBe("Modifié");
  });
});

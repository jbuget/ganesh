import { describe, expect, it } from "vitest";

import {
  NO_FILTER,
  writeFilters,
  hasActiveFilter,
  filterMissions,
  includesArchived,
  readFilters,
  type MissionFilters,
} from "./mission-filters";
import type { BoardCardResponse } from "@/lib/api/generated/model";

const card = (over: Record<string, unknown> = {}): BoardCardResponse =>
  ({
    consumed_days: 0,
    contributors: [{ id: 1, display_name: "Léa Chen", initials: "LC" }],
    comments: 0,
    sub_projects: 0,
    parent: null,
    ...over,
    project: {
      id: 1,
      label: "Portail bailleurs",
      kind: "project",
      status: "development",
      parent_id: null,
      is_active: true,
      estimated_days: 20,
      category: "innovate_differentiate",
      go_live_date: null,
      position: 0,
      monday_item_id: null,
      monday_subitem_id: null,
      is_syncable_to_monday: false,
      is_deletable: false,
      ...(over.project as object),
    },
  }) as BoardCardResponse;

const filters = (over: Partial<MissionFilters> = {}): MissionFilters => ({
  ...NO_FILTER,
  ...over,
});

describe("filtreActif", () => {
  it("sees no filter on empty criteria", () => {
    expect(hasActiveFilter(NO_FILTER)).toBe(false);
  });

  it("ignores a name made of spaces", () => {
    expect(hasActiveFilter(filters({ name: "   " }))).toBe(false);
  });

  it("triggers as soon as a criterion is set", () => {
    expect(hasActiveFilter(filters({ phases: ["scoping"] }))).toBe(true);
    expect(hasActiveFilter(filters({ name: "portail" }))).toBe(true);
  });
});

describe("searching by name", () => {
  it("keeps a mission whose name contains the search", () => {
    expect(filterMissions([card()], filters({ name: "bailleurs" }))).toHaveLength(1);
  });

  it("ignores case and accents", () => {
    const cards = [card({ project: { label: "Refonte extranet copropriété" } })];

    expect(filterMissions(cards, filters({ name: "COPROPRIETE" }))).toHaveLength(1);
  });

  it("rules out what does not match", () => {
    expect(filterMissions([card()], filters({ name: "facturation" }))).toHaveLength(0);
  });
});

describe("multiple-choice criteria", () => {
  it("keeps the missions of one of the chosen categories", () => {
    const cards = [
      card({ project: { id: 1, category: "innovate_differentiate" } }),
      card({ project: { id: 2, category: "structure_platform" } }),
      card({ project: { id: 3, category: null } }),
    ];

    const kept = filterMissions(
      cards,
      filters({ categories: ["innovate_differentiate", "structure_platform"] }),
    );

    expect(kept.map((c) => c.project.id)).toEqual([1, 2]);
  });

  it("keeps the missions of one of the chosen priorities", () => {
    const cards = [
      card({ project: { id: 1, priority: "critical" } }),
      card({ project: { id: 2, priority: "low" } }),
      card({ project: { id: 3, priority: null } }),
    ];

    const kept = filterMissions(cards, filters({ priorities: ["critical"] }));

    expect(kept.map((c) => c.project.id)).toEqual([1]);
  });

  it("keeps the missions carried by one of the chosen contributors", () => {
    const cards = [
      card({ project: { id: 1 }, contributors: [{ id: 7 } as never] }),
      card({ project: { id: 2 }, contributors: [] }),
    ];

    const kept = filterMissions(cards, filters({ contributors: [7] }));

    expect(kept.map((c) => c.project.id)).toEqual([1]);
  });

  it("tells projects from their sub-projects", () => {
    const cards = [
      card({ project: { id: 1, kind: "project" } }),
      card({ project: { id: 2, kind: "work_package", parent_id: 1 } }),
    ];

    expect(
      filterMissions(cards, filters({ types: ["work_package"] })).map(
        (c) => c.project.id,
      ),
    ).toEqual([2]);
    expect(
      filterMissions(cards, filters({ types: ["project", "work_package"] })),
    ).toHaveLength(2);
  });

  it("combines the criteria: all must be satisfied", () => {
    const cards = [
      card({
        project: { id: 1, label: "Portail", category: "innovate_differentiate" },
      }),
      card({
        project: { id: 2, label: "Portail", category: "structure_platform" },
      }),
    ];

    const kept = filterMissions(
      cards,
      filters({ name: "portail", categories: ["structure_platform"] }),
    );

    expect(kept.map((c) => c.project.id)).toEqual([2]);
  });
});

describe("archived missions", () => {
  const cards = [
    card({ project: { id: 1, is_active: true } }),
    card({ project: { id: 2, is_active: false } }),
  ];

  it("rules them out until they are asked for", () => {
    const kept = filterMissions(cards, NO_FILTER);

    expect(kept.map((c) => c.project.id)).toEqual([1]);
  });

  it("shows only them when only they are asked for", () => {
    const kept = filterMissions(cards, filters({ states: ["archived"] }));

    expect(kept.map((c) => c.project.id)).toEqual([2]);
  });

  it("shows both when both states are ticked", () => {
    const kept = filterMissions(cards, filters({ states: ["active", "archived"] }));

    expect(kept.map((c) => c.project.id)).toEqual([1, 2]);
  });

  it("asks the server for them again only when they are wanted", () => {
    expect(includesArchived(NO_FILTER)).toBe(false);
    expect(includesArchived(filters({ states: ["active"] }))).toBe(false);
    expect(includesArchived(filters({ states: ["archived"] }))).toBe(true);
  });

  it("counts as a filter: the board is no longer the steering view", () => {
    expect(hasActiveFilter(filters({ states: ["archived"] }))).toBe(true);
  });
});

describe("filtrage par phase", () => {
  const cards = [
    card({ project: { id: 1, status: "development" } }),
    card({ project: { id: 2, status: "scoping" } }),
  ];

  it("keeps every mission when no phase is chosen", () => {
    expect(filterMissions(cards, NO_FILTER)).toHaveLength(2);
  });

  it("keeps only the missions of the chosen phases", () => {
    const kept = filterMissions(cards, filters({ phases: ["development"] }));

    expect(kept.map((c) => c.project.id)).toEqual([1]);
  });
});

describe("filters held by the URL", () => {
  it("reads back what it wrote", () => {
    const chosen = filters({
      name: "portail",
      phases: ["scoping", "development"],
      categories: ["innovate_differentiate"],
      priorities: ["high"],
      contributors: [3, 7],
      types: ["work_package"],
      states: ["archived"],
    });

    const params = new URLSearchParams();
    writeFilters(params, chosen);

    expect(readFilters(params)).toEqual(chosen);
  });

  it("writes nothing when no filter is set", () => {
    const params = new URLSearchParams("mission=12");
    writeFilters(params, NO_FILTER);

    expect(params.toString()).toBe("mission=12");
  });

  it("leaves the other parameters in place", () => {
    const params = new URLSearchParams("mission=12&phase=scoping");
    writeFilters(params, filters({ phases: ["development"] }));

    expect(params.get("mission")).toBe("12");
    expect(params.getAll("phase")).toEqual(["development"]);
  });

  it("ignores an unknown value rather than emptying the screen", () => {
    const params = new URLSearchParams("phase=sieste&contributor=abc");

    expect(readFilters(params)).toEqual(NO_FILTER);
  });
});

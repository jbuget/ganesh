import { describe, expect, it } from "vitest";

import type { ProjectListItemResponse } from "@/lib/api/generated/model";
import {
  NO_SORT,
  sortComparator,
  writeSort,
  readSort,
  nextSort,
  type MissionSort,
} from "@/lib/mission-sort";

const cost = (build = 0, run = 0, estimated: number | null = null) => ({
  build_days: build,
  run_days: run,
  estimated_days: estimated,
  monthly_run_rate: null,
  has_overrun: estimated != null && build > estimated,
});

const mission = (
  label: string,
  fields: Partial<ProjectListItemResponse["project"]> = {},
  spent: { build?: number; run?: number } = {},
): ProjectListItemResponse =>
  ({
    project: {
      id: label.length,
      label,
      kind: "project",
      status: "exploration",
      priority: null,
      category: null,
      estimated_days: null,
      ...fields,
    },
    leads: [],
    contributors: [],
    cost: cost(spent.build, spent.run, fields.estimated_days ?? null),
    tree_cost: cost(spent.build, spent.run, fields.estimated_days ?? null),
    delivered_days: (spent.build ?? 0) + (spent.run ?? 0),
    comments: 0,
    latest_update: null,
  }) as ProjectListItemResponse;

const labels = (missions: ProjectListItemResponse[], sorted: MissionSort) =>
  [...missions].sort(sortComparator(sorted)).map((m) => m.project.label);

describe("the reference list order", () => {
  it("arranges by phase then by name when no column is asked for", () => {
    const missions = [
      mission("Zèbre", { status: "exploration" }),
      mission("Alpha", { status: "operations" }),
      mission("Bravo", { status: "exploration" }),
    ];

    expect(labels(missions, NO_SORT)).toEqual(["Bravo", "Zèbre", "Alpha"]);
  });

  it("arranges by name, accents included", () => {
    const missions = [mission("Zèbre"), mission("Éclair"), mission("Alpha")];

    expect(labels(missions, { column: "project", direction: "asc" })).toEqual([
      "Alpha",
      "Éclair",
      "Zèbre",
    ]);
  });

  it("reverses the order when descending", () => {
    const missions = [mission("Alpha"), mission("Zèbre")];

    expect(labels(missions, { column: "project", direction: "desc" })).toEqual([
      "Zèbre",
      "Alpha",
    ]);
  });

  it("arranges phases in life-cycle order, not alphabetically", () => {
    const missions = [
      mission("Zèbre", { status: "operations" }),
      mission("Alpha", { status: "scoping" }),
      mission("Bravo", { status: "exploration" }),
    ];

    expect(labels(missions, { column: "phase", direction: "asc" })).toEqual([
      "Bravo",
      "Alpha",
      "Zèbre",
    ]);
  });

  it("arranges priorities from strongest to weakest", () => {
    const missions = [
      mission("Basse", { priority: "low" }),
      mission("Critique", { priority: "critical" }),
      mission("Normale", { priority: "normal" }),
    ];

    expect(labels(missions, { column: "priority", direction: "asc" })).toEqual([
      "Critique",
      "Normale",
      "Basse",
    ]);
  });

  it("arranges builds by value, not by how they are written", () => {
    const missions = [
      mission("Neuf", {}, { build: 9 }),
      mission("Dix", {}, { build: 10 }),
    ];

    expect(labels(missions, { column: "build", direction: "asc" })).toEqual([
      "Neuf",
      "Dix",
    ]);
  });

  it("arranges run days by value", () => {
    const missions = [
      mission("Beaucoup", {}, { run: 12 }),
      mission("Peu", {}, { run: 3 }),
    ];

    expect(labels(missions, { column: "run", direction: "asc" })).toEqual([
      "Peu",
      "Beaucoup",
    ]);
  });

  it("leaves missing values at the end of the list, in both directions", () => {
    // A missing estimate is not a small estimate: it has nothing to say, and
    // must not sit at the top when one is looking for the big jobs.
    const missions = [mission("Sans"), mission("Avec", {}, { build: 5 })];

    expect(labels(missions, { column: "build", direction: "asc" })).toEqual([
      "Avec",
      "Sans",
    ]);
    expect(labels(missions, { column: "build", direction: "desc" })).toEqual([
      "Avec",
      "Sans",
    ]);
  });

  it("settles by name two missions the column ties", () => {
    const missions = [
      mission("Zèbre", {}, { build: 5 }),
      mission("Alpha", {}, { build: 5 }),
    ];

    expect(labels(missions, { column: "build", direction: "asc" })).toEqual([
      "Alpha",
      "Zèbre",
    ]);
  });
});

describe("the cycle of a column", () => {
  it("starts ascending on the first click", () => {
    expect(nextSort(NO_SORT, "build")).toEqual({
      column: "build",
      direction: "asc",
    });
  });

  it("moves to descending on the second", () => {
    expect(nextSort({ column: "build", direction: "asc" }, "build")).toEqual({
      column: "build",
      direction: "desc",
    });
  });

  it("returns to the reference list order on the third", () => {
    expect(nextSort({ column: "build", direction: "desc" }, "build")).toEqual(NO_SORT);
  });

  it("starts ascending again when the column changes", () => {
    expect(nextSort({ column: "build", direction: "desc" }, "phase")).toEqual({
      column: "phase",
      direction: "asc",
    });
  });
});

describe("the sort in the address", () => {
  it("reads no sort from a bare address", () => {
    expect(readSort(new URLSearchParams())).toEqual(NO_SORT);
  });

  it("reads back the sort it wrote", () => {
    const params = new URLSearchParams();
    writeSort(params, { column: "priority", direction: "desc" });

    expect(readSort(params)).toEqual({ column: "priority", direction: "desc" });
  });

  it("clears the sort from the address when the default order returns", () => {
    const params = new URLSearchParams("sort=phase&direction=desc");
    writeSort(params, NO_SORT);

    expect(params.toString()).toBe("");
  });

  it("ignores an unknown column rather than sorting at random", () => {
    expect(readSort(new URLSearchParams("sort=licorne&direction=asc"))).toEqual(
      NO_SORT,
    );
  });

  it("keeps ascending order when the direction is unreadable", () => {
    expect(readSort(new URLSearchParams("sort=phase&direction=lateral"))).toEqual({
      column: "phase",
      direction: "asc",
    });
  });

  it("leaves the address's other parameters in place", () => {
    const params = new URLSearchParams("phase=scoping");
    writeSort(params, { column: "project", direction: "asc" });

    expect(params.get("phase")).toBe("scoping");
  });
});

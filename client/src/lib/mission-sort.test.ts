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

const mission = (
  label: string,
  fields: Partial<ProjectListItemResponse["project"]> = {},
  delivered = 0,
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
    delivered_days: delivered,
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

  it("arranges estimates by value, not by how they are written", () => {
    const missions = [
      mission("Neuf", { estimated_days: 9 }),
      mission("Dix", { estimated_days: 10 }),
    ];

    expect(labels(missions, { column: "estimated", direction: "asc" })).toEqual([
      "Neuf",
      "Dix",
    ]);
  });

  it("arranges delivered days by value", () => {
    const missions = [mission("Beaucoup", {}, 12), mission("Peu", {}, 3)];

    expect(labels(missions, { column: "delivered", direction: "asc" })).toEqual([
      "Peu",
      "Beaucoup",
    ]);
  });

  it("leaves missing values at the end of the list, in both directions", () => {
    // A missing estimate is not a small estimate: it has nothing to say, and
    // must not sit at the top when one is looking for the big jobs.
    const missions = [
      mission("Sans", { estimated_days: null }),
      mission("Avec", { estimated_days: 5 }),
    ];

    expect(labels(missions, { column: "estimated", direction: "asc" })).toEqual([
      "Avec",
      "Sans",
    ]);
    expect(labels(missions, { column: "estimated", direction: "desc" })).toEqual([
      "Avec",
      "Sans",
    ]);
  });

  it("settles by name two missions the column ties", () => {
    const missions = [
      mission("Zèbre", { estimated_days: 5 }),
      mission("Alpha", { estimated_days: 5 }),
    ];

    expect(labels(missions, { column: "estimated", direction: "asc" })).toEqual([
      "Alpha",
      "Zèbre",
    ]);
  });
});

describe("the cycle of a column", () => {
  it("starts ascending on the first click", () => {
    expect(nextSort(NO_SORT, "estimated")).toEqual({
      column: "estimated",
      direction: "asc",
    });
  });

  it("moves to descending on the second", () => {
    expect(nextSort({ column: "estimated", direction: "asc" }, "estimated")).toEqual({
      column: "estimated",
      direction: "desc",
    });
  });

  it("returns to the reference list order on the third", () => {
    expect(nextSort({ column: "estimated", direction: "desc" }, "estimated")).toEqual(
      NO_SORT,
    );
  });

  it("starts ascending again when the column changes", () => {
    expect(nextSort({ column: "estimated", direction: "desc" }, "phase")).toEqual({
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

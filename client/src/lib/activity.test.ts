import { describe, expect, it } from "vitest";

import type {
  ActivityLineResponse,
  ActivitySummaryResponse,
} from "@/lib/api/generated/model";

import {
  ACTIVITY_RANGES,
  awayContributors,
  comparedWith,
  formatDays,
  formatMovement,
  missionsOf,
  silentContributors,
} from "./activity";

describe("activity windows", () => {
  it("offers anchored windows only", () => {
    // A rolling week straddles two weeks; « la semaine dernière » does not.
    expect(ACTIVITY_RANGES.map((range) => range.value)).toEqual([
      "this_week",
      "last_week",
      "last_two_weeks",
      "this_month",
      "last_month",
    ]);
  });
});

describe("formatDays", () => {
  it("draws nothing declared as an em dash, never as a zero", () => {
    expect(formatDays(0)).toBe("—");
  });

  it("says a half day the French way", () => {
    expect(formatDays(0.5)).toBe("0,5");
  });

  it("drops a trailing zero", () => {
    expect(formatDays(3)).toBe("3");
  });
});

describe("formatMovement", () => {
  it("says nothing when the line did not move", () => {
    // A « +0 j » would claim a stability that is only an absence of change.
    expect(formatMovement(0)).toBeNull();
  });

  it("signs a rise", () => {
    expect(formatMovement(2.5)).toBe("+2,5 j");
  });

  it("uses a true minus sign for a fall", () => {
    expect(formatMovement(-3)).toBe("−3 j");
  });
});

describe("comparedWith", () => {
  it("names a running month as the same stretch of the one before", () => {
    // Not « le mois dernier »: a month still running is compared against as
    // much of the one before, and a reader who assumes otherwise misreads
    // every movement on the screen.
    expect(comparedWith("this_month")).toBe("à la même période du mois précédent");
  });

  it("contracts the article rather than leaving « à le »", () => {
    // « à le mois d'avant » is what concatenation produces, and neither the
    // type checker nor a test asserting on a figure ever sees it.
    expect(comparedWith("last_month")).toBe("au mois d'avant");
  });

  it("contracts a plural the same way", () => {
    expect(comparedWith("last_two_weeks")).toBe("aux deux semaines d'avant");
  });

  it("falls back on a plain wording for a window it does not know", () => {
    expect(comparedWith("last_90_days")).toBe("à la période précédente");
  });
});

describe("missionsOf", () => {
  function aLine(over: Partial<ActivityLineResponse> = {}): ActivityLineResponse {
    return {
      project_id: 1,
      label: "WAATcher",
      kind: "project",
      status: null,
      category: null,
      days_by_contributor: {},
      own_days_by_contributor: {},
      days: 0,
      own_days: 0,
      share: null,
      movement: 0,
      is_new: false,
      packages: [],
      ...over,
    };
  }

  function aSummary(
    projects: ActivityLineResponse[],
    offProject: ActivityLineResponse[] = [],
  ): ActivitySummaryResponse {
    return {
      period: {
        range: "last_week",
        start: "2026-09-07",
        end: "2026-09-13",
        working_days: 5,
      },
      contributors: [],
      projects,
      off_project: offProject,
      project_days: 0,
      off_project_days: 0,
      declared_days: 0,
      expected_days: 0,
      coverage: null,
    };
  }

  it("keeps only what this person put time on", () => {
    const summary = aSummary([
      aLine({ project_id: 1, label: "WAATcher", days_by_contributor: { 7: 3 } }),
      aLine({ project_id: 2, label: "NOMAD", days_by_contributor: { 8: 4 } }),
    ]);

    expect(missionsOf(summary, 7).map((m) => m.label)).toEqual(["WAATcher"]);
  });

  it("reads the heaviest mission first", () => {
    const summary = aSummary([
      aLine({ project_id: 1, label: "Petit", days_by_contributor: { 7: 1 } }),
      aLine({ project_id: 2, label: "Gros", days_by_contributor: { 7: 4 } }),
    ]);

    expect(missionsOf(summary, 7).map((m) => m.label)).toEqual(["Gros", "Petit"]);
  });

  it("counts a project with its packages, as the mission count beside it does", () => {
    // days_by_contributor is already rolled up: four packages of one product
    // are one mission everywhere else on the screen.
    const summary = aSummary([
      aLine({ project_id: 1, label: "WAATcher", days_by_contributor: { 7: 5 } }),
    ]);

    expect(missionsOf(summary, 7)[0].days).toBe(5);
  });

  it("keeps off-project work, and says that is what it is", () => {
    // 5 days of which 3 on leave is not a week spent the way the bare total
    // suggests.
    const summary = aSummary(
      [aLine({ project_id: 1, label: "WAATcher", days_by_contributor: { 7: 2 } })],
      [aLine({ project_id: 9, label: "Congés", days_by_contributor: { 7: 3 } })],
    );

    expect(missionsOf(summary, 7)).toEqual([
      { projectId: 1, label: "WAATcher", days: 2, isOffProject: false },
      { projectId: 9, label: "Congés", days: 3, isOffProject: true },
    ]);
  });

  it("puts off-project work after the missions, however heavy it is", () => {
    // Three days of leave weigh more than one on a mission, and still read
    // last: the missions are what the window is opened for.
    const summary = aSummary(
      [aLine({ project_id: 1, label: "WAATcher", days_by_contributor: { 7: 1 } })],
      [aLine({ project_id: 9, label: "Congés", days_by_contributor: { 7: 3 } })],
    );

    expect(missionsOf(summary, 7).map((m) => m.label)).toEqual(["WAATcher", "Congés"]);
  });

  it("says nothing for someone who declared nothing", () => {
    const summary = aSummary([aLine({ project_id: 1, days_by_contributor: { 7: 3 } })]);

    expect(missionsOf(summary, 99)).toEqual([]);
  });
});

describe("who the window names, and who it only counts", () => {
  function aContributor(
    display_name: string,
    expected_days: number,
    declared_days: number,
  ) {
    return {
      id: 1,
      display_name,
      expected_days,
      declared_days,
      coverage: expected_days === 0 ? null : declared_days / expected_days,
      missions: 0,
    };
  }

  it("names whoever owed something and declared nothing", () => {
    const silent = silentContributors([
      aContributor("Léa", 22, 0),
      aContributor("Malik", 22, 12),
    ]);

    expect(silent).toEqual(["Léa"]);
  });

  it("leaves out whoever the window expects nothing of", () => {
    // On leave: nothing declared, nothing owed. Listing them under « n'ont
    // rien déclaré » would reproach an absence the register was told about.
    const silent = silentContributors([
      aContributor("Léa", 0, 0),
      aContributor("Malik", 22, 0),
    ]);

    expect(silent).toEqual(["Malik"]);
  });

  it("counts those the window expects nothing of, without naming them", () => {
    // So that nobody away is quietly forgotten: they show in no coverage and
    // hold no capacity, and the count is what puts them back in plain sight.
    const away = awayContributors([
      aContributor("Léa", 0, 0),
      aContributor("Nour", 0, 0),
      aContributor("Malik", 22, 12),
    ]);

    expect(away).toBe(2);
  });
});

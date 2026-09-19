import { describe, expect, it } from "vitest";

import { daysMissingEntry, latestUpdates, monthsToSettle, myMissions } from "./home";
import type {
  MonthGridResponse,
  ProjectListItemResponse,
  ProjectResponse,
} from "@/lib/api/generated/model";

const project = (
  id: number,
  label: string,
  fields: Partial<ProjectResponse> = {},
): ProjectResponse =>
  ({
    id,
    label,
    kind: "project",
    status: null,
    parent_id: null,
    is_active: true,
    estimated_days: null,
    priority: null,
    ...fields,
  }) as ProjectResponse;

const member = (id: number) => ({
  id,
  display_name: `U${id}`,
  initials: `U${id}`,
});

const listed = (
  item: ProjectResponse,
  contributors: number[],
  fields: Partial<ProjectListItemResponse> = {},
): ProjectListItemResponse =>
  ({
    project: item,
    contributors: contributors.map(member),
    leads: [],
    latest_update: null,
    ...fields,
  }) as ProjectListItemResponse;

const grid = (
  rows: { project_id: number; total: number }[],
  days: { day: string; is_off_day: boolean }[] = [],
  dayTotals: { day: string; total: number }[] = [],
): MonthGridResponse =>
  ({
    rows: rows.map((row) => ({ ...row, label: "" })),
    days,
    day_totals: dayTotals,
  }) as MonthGridResponse;

const month = (
  is_writable: boolean,
  actual_total = 0,
  forecast_total = 0,
): MonthGridResponse =>
  ({ is_writable, actual_total, forecast_total }) as MonthGridResponse;

describe("monthsToSettle", () => {
  const AUGUST = { year: 2026, month: 8 };
  const JULY = { year: 2026, month: 7 };
  const JUNE = { year: 2026, month: 6 };

  it("keeps the months still open", () => {
    const open = monthsToSettle([
      { cursor: AUGUST, grid: month(true, 18) },
      { cursor: JULY, grid: month(false, 20) },
      { cursor: JUNE, grid: month(true, 21) },
    ]);

    expect(open.map((m) => m.month)).toEqual([8, 6]);
  });

  it("tells a month left unentered from a month left unvalidated", () => {
    const open = monthsToSettle([
      { cursor: AUGUST, grid: month(true, 18) },
      { cursor: JULY, grid: month(true) },
    ]);

    expect(open[0].isEmpty).toBe(false);
    expect(open[1].isEmpty).toBe(true);
  });

  it("counts a month carrying forecast alone as entered: something was said about it", () => {
    const open = monthsToSettle([{ cursor: AUGUST, grid: month(true, 0, 4) }]);

    expect(open[0].isEmpty).toBe(false);
  });

  it("keeps the order it is given: the closest month first", () => {
    const open = monthsToSettle([
      { cursor: AUGUST, grid: month(true) },
      { cursor: JULY, grid: month(true) },
      { cursor: JUNE, grid: month(true) },
    ]);

    expect(open.map((m) => m.month)).toEqual([8, 7, 6]);
  });

  it("says nothing about a month it has not received", () => {
    expect(monthsToSettle([{ cursor: AUGUST, grid: undefined }])).toEqual([]);
  });
});

describe("daysMissingEntry", () => {
  const DAYS = [
    { day: "2026-09-14", is_off_day: false },
    { day: "2026-09-15", is_off_day: false },
    { day: "2026-09-16", is_off_day: false },
    // A public holiday, or a Saturday: nothing is expected on it.
    { day: "2026-09-17", is_off_day: true },
    { day: "2026-09-18", is_off_day: false },
  ];

  it("names the working days gone by with nothing on them", () => {
    const month = grid([], DAYS, [
      { day: "2026-09-14", total: 1 },
      { day: "2026-09-16", total: 0.5 },
    ]);

    expect(daysMissingEntry(month, "2026-09-18")).toEqual(["2026-09-15"]);
  });

  it("says nothing about a non-working day", () => {
    const month = grid([], DAYS, []);

    expect(daysMissingEntry(month, "2026-09-20")).not.toContain("2026-09-17");
  });

  it("leaves today alone: a day under way is not a gap yet", () => {
    const month = grid([], DAYS, [{ day: "2026-09-14", total: 1 }]);

    expect(daysMissingEntry(month, "2026-09-15")).toEqual([]);
  });

  it("says nothing about a month it has not received", () => {
    expect(daysMissingEntry(undefined, "2026-09-18")).toEqual([]);
  });
});

describe("myMissions", () => {
  const PORTAL = project(1, "Portail bailleurs", { status: "development" });
  const ABSENCES = project(2, "Absences", { kind: "off_project" });
  const LOT = project(3, "Lot 1", { status: "scoping" });
  const OTHER = project(4, "Refonte extranet", { status: "development" });

  const MISSIONS = [
    listed(PORTAL, [7]),
    listed(ABSENCES, []),
    listed(LOT, [], { leads: [member(7)] }),
    listed(OTHER, [9]),
  ];

  it("keeps what one contributes to, even with no time entered yet", () => {
    const mine = myMissions(MISSIONS, 7, grid([]), grid([]));

    expect(mine.map((m) => m.item.project.label)).toEqual(["Portail bailleurs"]);
    expect(mine[0].isContributor).toBe(true);
  });

  it("keeps what one declared time on this month, without being a contributor", () => {
    const mine = myMissions(MISSIONS, 7, grid([{ project_id: 2, total: 2 }]), grid([]));

    expect(mine.map((m) => m.item.project.label)).toContain("Absences");
  });

  it("keeps what one declared time on last month: recent work still counts", () => {
    const mine = myMissions(MISSIONS, 7, grid([]), grid([{ project_id: 4, total: 3 }]));

    expect(mine.map((m) => m.item.project.label)).toContain("Refonte extranet");
  });

  it("does not keep a row put on the month with nothing entered on it", () => {
    const mine = myMissions(MISSIONS, 7, grid([{ project_id: 4, total: 0 }]), grid([]));

    expect(mine.map((m) => m.item.project.label)).not.toContain("Refonte extranet");
  });

  it("does not count being a lead: answering for a mission is not working on it", () => {
    const mine = myMissions(MISSIONS, 7, grid([]), grid([]));

    expect(mine.map((m) => m.item.project.label)).not.toContain("Lot 1");
  });

  it("carries the days of the month running, and only those", () => {
    const mine = myMissions(
      MISSIONS,
      7,
      grid([{ project_id: 1, total: 4.5 }]),
      grid([{ project_id: 1, total: 12 }]),
    );

    expect(mine[0].days).toBe(4.5);
  });

  it("puts what takes the most time first, then follows the phase order", () => {
    const mine = myMissions(
      [listed(LOT, [7]), listed(PORTAL, [7]), listed(OTHER, [7])],
      7,
      grid([{ project_id: 4, total: 6 }]),
      grid([]),
    );

    expect(mine.map((m) => m.item.project.label)).toEqual([
      // Six days this month.
      "Refonte extranet",
      // Both at zero: cadrage comes before réalisation, as on the board.
      "Lot 1",
      "Portail bailleurs",
    ]);
  });

  it("names what a work package hangs from: its label alone says nothing", () => {
    const packageOf = project(5, "Lot 2", { parent_id: 1 });
    const mine = myMissions(
      [listed(PORTAL, [7]), listed(packageOf, [7])],
      7,
      grid([]),
      grid([]),
    );

    expect(mine.find((m) => m.item.project.id === 5)?.parentLabel).toBe(
      "Portail bailleurs",
    );
    expect(mine.find((m) => m.item.project.id === 1)?.parentLabel).toBeNull();
  });

  it("has nothing to say about nobody", () => {
    expect(myMissions(MISSIONS, null, grid([]), grid([]))).toEqual([]);
  });
});

describe("latestUpdates", () => {
  const update = (at: string) => ({
    author: member(9),
    body: "Recette terminée",
    published_at: at,
  });

  const mine = [
    { item: listed(project(1, "A"), [7], { latest_update: update("2026-09-10") }) },
    { item: listed(project(2, "B"), [7]) },
    { item: listed(project(3, "C"), [7], { latest_update: update("2026-09-18") }) },
  ].map((m) => ({ ...m, days: 0, isContributor: true, parentLabel: null }));

  it("reads the most recent news first", () => {
    expect(latestUpdates(mine, 10).map((u) => u.item.project.label)).toEqual([
      "C",
      "A",
    ]);
  });

  it("says nothing about a mission whose thread is empty", () => {
    expect(latestUpdates(mine, 10).map((u) => u.item.project.label)).not.toContain("B");
  });

  it("stops at the number of entries asked for", () => {
    expect(latestUpdates(mine, 1).map((u) => u.item.project.label)).toEqual(["C"]);
  });
});

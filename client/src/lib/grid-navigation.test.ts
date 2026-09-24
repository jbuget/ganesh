import { describe, expect, it } from "vitest";

import {
  cellId,
  nextCell,
  parseCellId,
  tabStop,
  type NavigableGrid,
} from "@/lib/grid-navigation";

/**
 * Three missions over five days, the third day closed — a weekend, or a month
 * read after validation. A closed day is closed on every row, which is what
 * makes moving up and down over one of them come back with nothing.
 */
const GRID: NavigableGrid = {
  rows: [10, 20, 30],
  days: ["2026-09-01", "2026-09-02", "2026-09-03", "2026-09-04", "2026-09-05"],
  isOpen: (cell) => cell.day !== "2026-09-03",
};

describe("nextCell", () => {
  it("moves to the next day on the same row", () => {
    expect(nextCell(GRID, { projectId: 20, day: "2026-09-01" }, "ArrowRight")).toEqual({
      projectId: 20,
      day: "2026-09-02",
    });
  });

  it("moves to the previous day on the same row", () => {
    expect(nextCell(GRID, { projectId: 20, day: "2026-09-02" }, "ArrowLeft")).toEqual({
      projectId: 20,
      day: "2026-09-01",
    });
  });

  it("steps over a closed day rather than stopping on it", () => {
    expect(nextCell(GRID, { projectId: 20, day: "2026-09-02" }, "ArrowRight")).toEqual({
      projectId: 20,
      day: "2026-09-04",
    });
  });

  it("moves to the same day on the row below", () => {
    expect(nextCell(GRID, { projectId: 10, day: "2026-09-02" }, "ArrowDown")).toEqual({
      projectId: 20,
      day: "2026-09-02",
    });
  });

  it("moves to the same day on the row above", () => {
    expect(nextCell(GRID, { projectId: 30, day: "2026-09-02" }, "ArrowUp")).toEqual({
      projectId: 20,
      day: "2026-09-02",
    });
  });

  it("goes to the first open day of the row", () => {
    expect(nextCell(GRID, { projectId: 20, day: "2026-09-04" }, "Home")).toEqual({
      projectId: 20,
      day: "2026-09-01",
    });
  });

  it("goes to the last open day of the row", () => {
    expect(nextCell(GRID, { projectId: 20, day: "2026-09-01" }, "End")).toEqual({
      projectId: 20,
      day: "2026-09-05",
    });
  });

  it("stays put at the end of a row: a grid does not wrap", () => {
    expect(
      nextCell(GRID, { projectId: 20, day: "2026-09-05" }, "ArrowRight"),
    ).toBeNull();
  });

  it("stays put at the start of a row", () => {
    expect(
      nextCell(GRID, { projectId: 20, day: "2026-09-01" }, "ArrowLeft"),
    ).toBeNull();
  });

  it("stays put on the last row", () => {
    expect(
      nextCell(GRID, { projectId: 30, day: "2026-09-02" }, "ArrowDown"),
    ).toBeNull();
  });

  it("stays put on the first row", () => {
    expect(nextCell(GRID, { projectId: 10, day: "2026-09-02" }, "ArrowUp")).toBeNull();
  });

  it("answers nothing when the whole column is closed", () => {
    expect(
      nextCell(GRID, { projectId: 10, day: "2026-09-03" }, "ArrowDown"),
    ).toBeNull();
  });

  it("answers nothing for a cell the grid does not hold", () => {
    expect(
      nextCell(GRID, { projectId: 99, day: "2026-09-02" }, "ArrowRight"),
    ).toBeNull();
    expect(
      nextCell(GRID, { projectId: 10, day: "2026-10-01" }, "ArrowRight"),
    ).toBeNull();
  });

  it("answers nothing when every day of the row is closed", () => {
    const closed: NavigableGrid = { ...GRID, isOpen: () => false };
    expect(nextCell(closed, { projectId: 20, day: "2026-09-02" }, "Home")).toBeNull();
  });
});

describe("cellId", () => {
  it("names a cell and reads it back", () => {
    const cell = { projectId: 10, day: "2026-09-14" };
    expect(parseCellId(cellId(cell))).toEqual(cell);
  });

  it("reads nothing out of what names no cell", () => {
    expect(parseCellId(undefined)).toBeNull();
    expect(parseCellId("")).toBeNull();
    expect(parseCellId("total")).toBeNull();
  });
});

describe("tabStop", () => {
  it("is the first open cell before anybody has touched the grid", () => {
    expect(tabStop(GRID, null)).toEqual({ projectId: 10, day: "2026-09-01" });
  });

  it("follows the cursor once the hand has been somewhere", () => {
    const cursor = { projectId: 20, day: "2026-09-04" };
    expect(tabStop(GRID, cursor)).toEqual(cursor);
  });

  it("falls back to the first cell when the cursor names a row that has gone", () => {
    expect(tabStop(GRID, { projectId: 99, day: "2026-09-01" })).toEqual({
      projectId: 10,
      day: "2026-09-01",
    });
  });

  it("falls back when the cursor sits on a day that closed", () => {
    expect(tabStop(GRID, { projectId: 20, day: "2026-09-03" })).toEqual({
      projectId: 10,
      day: "2026-09-01",
    });
  });

  it("offers no stop at all on a grid nothing is open on", () => {
    // A validated month: there is nothing to move between, so the grid steps
    // out of the tab order rather than trapping a stop that writes nothing.
    expect(tabStop({ ...GRID, isOpen: () => false }, null)).toBeNull();
  });
});

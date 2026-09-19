import { describe, expect, it } from "vitest";

import {
  HIDEABLE_COLUMNS,
  NO_HIDDEN_COLUMN,
  hiddenColumns,
  readHiddenColumns,
  tableWidth,
  writeHiddenColumns,
  type ColumnKey,
} from "./mission-columns";

const params = (query: string) => new URLSearchParams(query);

describe("hideable columns", () => {
  it("offers every column but the two the row is read by", () => {
    expect(HIDEABLE_COLUMNS.map((column) => column.key)).toEqual([
      "phase",
      "priority",
      "category",
      "build",
      "run",
      "leads",
      "contributors",
      "links",
    ]);
  });
});

describe("readHiddenColumns", () => {
  it("hides nothing on a bare address: the panorama is the default", () => {
    expect(readHiddenColumns(params(""))).toEqual(NO_HIDDEN_COLUMN);
  });

  it("reads the columns put away", () => {
    expect(readHiddenColumns(params("hide=category,priority"))).toEqual(
      hiddenColumns(["category", "priority"]),
    );
  });

  /** A link typed by hand, or a column that has since disappeared. */
  it("ignores what names no column", () => {
    expect(readHiddenColumns(params("hide=category,quantième"))).toEqual(
      hiddenColumns(["category"]),
    );
  });
});

describe("writeHiddenColumns", () => {
  it("leaves no parameter when everything shows", () => {
    const written = params("sort=build");
    writeHiddenColumns(written, NO_HIDDEN_COLUMN);

    expect(written.toString()).toBe("sort=build");
  });

  it("writes the columns in the order of the table, whatever the order of the clicks", () => {
    const written = params("");
    writeHiddenColumns(written, hiddenColumns(["links", "phase"]));

    expect(written.get("hide")).toBe("phase,links");
  });

  it("leaves the other parameters alone", () => {
    const written = params("sort=build&direction=desc");
    writeHiddenColumns(written, hiddenColumns(["phase"]));

    expect(written.get("sort")).toBe("build");
    expect(written.get("direction")).toBe("desc");
  });
});

describe("tableWidth", () => {
  it("spans the full reference list when every column shows", () => {
    expect(tableWidth(NO_HIDDEN_COLUMN)).toBe(1500);
  });

  it("gives back exactly what a column put away was taking", () => {
    const category = HIDEABLE_COLUMNS.find((column) => column.key === "category");

    expect(tableWidth(hiddenColumns(["category"]))).toBe(1500 - category!.width);
  });

  /** Nothing left but the name and its thread: the row still reads. */
  it("keeps the two pinned columns when everything else is put away", () => {
    const every = HIDEABLE_COLUMNS.map((column) => column.key) as ColumnKey[];

    expect(tableWidth(hiddenColumns(every))).toBe(448);
  });
});

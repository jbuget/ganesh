import { describe, expect, it } from "vitest";

import { parseProjectsCsv } from "./csv-import";

describe("parseProjectsCsv", () => {
  it("reads a semicolon-separated file", () => {
    const lines = parseProjectsCsv("label;estime_j\nPortail;20");

    expect(lines).toHaveLength(1);
    expect(lines[0].label).toBe("Portail");
    expect(lines[0].estimated_days).toBe(20);
  });

  it("also reads a comma-separated file", () => {
    const lines = parseProjectsCsv("label,estime_j\nPortail,20");

    expect(lines[0].label).toBe("Portail");
    expect(lines[0].estimated_days).toBe(20);
  });

  it("does not care about the column order", () => {
    const lines = parseProjectsCsv("estime_j;label\n30;Extranet");

    expect(lines[0].label).toBe("Extranet");
    expect(lines[0].estimated_days).toBe(30);
  });

  it("ignores the columns it does not know", () => {
    const lines = parseProjectsCsv("label;Service / BU;estime_j\nPortail;DSI;20");

    expect(lines[0].label).toBe("Portail");
    expect(lines[0].estimated_days).toBe(20);
  });

  it("accepts a decimal comma", () => {
    expect(parseProjectsCsv("label;estime_j\nPortail;7,5")[0].estimated_days).toBe(7.5);
  });

  it("leaves the estimate empty rather than inventing a zero", () => {
    expect(parseProjectsCsv("label;estime_j\nPortail;")[0].estimated_days).toBeNull();
  });

  it("attaches a work package to its project by label", () => {
    const lines = parseProjectsCsv("label;kind;parent_label\nLot API;lot;Portail");

    expect(lines[0].kind).toBe("work_package");
    expect(lines[0].parent_label).toBe("Portail");
  });

  it("treats a mission as a project by default", () => {
    expect(parseProjectsCsv("label\nPortail")[0].kind).toBe("project");
  });

  it("strips the surrounding quotes", () => {
    expect(parseProjectsCsv('label\n"Portail bailleurs"')[0].label).toBe(
      "Portail bailleurs",
    );
  });

  it("ignores empty lines", () => {
    expect(parseProjectsCsv("label\nPortail\n\n\nExtranet")).toHaveLength(2);
  });

  it("returns nothing for a file with no data", () => {
    expect(parseProjectsCsv("label;estime_j")).toEqual([]);
    expect(parseProjectsCsv("")).toEqual([]);
  });
});

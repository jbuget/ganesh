import { describe, expect, it } from "vitest";

import type { RequestResponse } from "@/lib/api/generated/model";
import {
  EVERY_REQUEST,
  NO_REQUEST_FILTER,
  filterRequests,
  readRequestFilters,
  writeRequestFilters,
} from "@/lib/request-filters";

function need(title: string, over: Partial<RequestResponse> = {}): RequestResponse {
  return {
    id: title.length,
    title,
    state: "submitted",
    requester: { id: 7, label: "Anne Métier" },
    sponsors: [{ id: 3, label: "C. Direction" }],
    departments: ["finance_admin"],
    created_at: "2026-09-22T10:00:00Z",
    ...over,
  };
}

const titles = (requests: RequestResponse[]) => requests.map((r) => r.title);

describe("filterRequests", () => {
  it("opens on what still waits on somebody", () => {
    // « Plus tard » answers nothing, it postpones: left out of sight, it is
    // a need nobody ever comes back to.
    const needs = [
      need("En attente"),
      need("Pas ce trimestre", { state: "deferred" }),
      need("Vieille", { state: "rejected" }),
      need("Batie", { state: "converted" }),
    ];

    expect(titles(filterRequests(needs, NO_REQUEST_FILTER))).toEqual([
      "En attente",
      "Pas ce trimestre",
    ]);
  });

  it("shows everything once no state is asked for", () => {
    const needs = [need("En attente"), need("Vieille", { state: "rejected" })];

    expect(titles(filterRequests(needs, EVERY_REQUEST))).toHaveLength(2);
  });

  it("searches the title and whoever filed it alike", () => {
    const needs = [
      need("Relances"),
      need("Autre", { requester: { id: 9, label: "Bruno Compta" } }),
    ];

    expect(
      titles(filterRequests(needs, { ...EVERY_REQUEST, search: "compta" })),
    ).toEqual(["Autre"]);
  });

  it("ignores case and accents", () => {
    expect(
      titles(filterRequests([need("Échéances")], { ...EVERY_REQUEST, search: "eche" })),
    ).toEqual(["Échéances"]);
  });

  it("keeps a need concerning any of the departments asked for", () => {
    const needs = [need("Compta"), need("Ailleurs", { departments: ["operations"] })];

    expect(
      titles(filterRequests(needs, { ...EVERY_REQUEST, departments: ["operations"] })),
    ).toEqual(["Ailleurs"]);
  });
});

describe("the filters in the address", () => {
  it("opens on what is waiting when the address says nothing", () => {
    expect(readRequestFilters(new URLSearchParams()).states).toEqual([
      "submitted",
      "deferred",
    ]);
  });

  it("writes « every state » down, since an empty list cannot say it", () => {
    const params = new URLSearchParams();
    writeRequestFilters(params, EVERY_REQUEST);

    expect(params.getAll("state")).toEqual(["all"]);
    expect(readRequestFilters(params).states).toEqual([]);
  });

  it("carries a state that was asked for", () => {
    const params = new URLSearchParams();
    writeRequestFilters(params, { ...EVERY_REQUEST, states: ["accepted"] });

    expect(readRequestFilters(params).states).toEqual(["accepted"]);
  });

  it("ignores a state nobody can read", () => {
    const params = new URLSearchParams("state=n-importe-quoi");

    expect(readRequestFilters(params).states).toEqual([]);
  });
});

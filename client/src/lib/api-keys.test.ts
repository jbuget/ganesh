import { describe, expect, it } from "vitest";

import type { ApiKeyResponse } from "@/lib/api/generated/model";
import { isUsable, oneYearFromNow, scopeLabel, sortKeys } from "@/lib/api-keys";

const key = (overrides: Partial<ApiKeyResponse> = {}) =>
  ({
    id: 1,
    name: "CI waat-tools",
    masked: "jns_abcdef123456",
    scopes: ["catalog:read"],
    created_at: "2026-01-01T10:00:00",
    state: "active",
    ...overrides,
  }) as unknown as ApiKeyResponse;

describe("scopeLabel", () => {
  it("reads a scope in French", () => {
    expect(scopeLabel("catalog:read")).toBe("Catalogue");
  });

  it("falls back to the raw scope rather than showing nothing", () => {
    expect(scopeLabel("future:scope" as never)).toBe("future:scope");
  });
});

describe("isUsable", () => {
  it("an active key still opens a door", () => {
    expect(isUsable(key())).toBe(true);
  });

  it("an expired one does not", () => {
    expect(isUsable(key({ state: "expired" }))).toBe(false);
  });

  it("a revoked one does not", () => {
    expect(isUsable(key({ state: "revoked" }))).toBe(false);
  });
});

describe("sortKeys", () => {
  it("puts what still opens a door first", () => {
    const sorted = sortKeys([
      key({ id: 1, state: "revoked", created_at: "2026-06-01T10:00:00" }),
      key({ id: 2, state: "active", created_at: "2026-01-01T10:00:00" }),
    ]);
    expect(sorted.map((k) => k.id)).toEqual([2, 1]);
  });

  it("orders each lot newest first", () => {
    const sorted = sortKeys([
      key({ id: 1, created_at: "2026-01-01T10:00:00" }),
      key({ id: 2, created_at: "2026-06-01T10:00:00" }),
    ]);
    expect(sorted.map((k) => k.id)).toEqual([2, 1]);
  });

  it("does not touch the list it was given", () => {
    const given = [key({ id: 1, state: "revoked" }), key({ id: 2 })];
    const before = [...given];
    sortKeys(given);
    expect(given).toEqual(before);
  });

  it("keeps a revoked key rather than dropping it", () => {
    // The audit refers to it: « revoked three months ago » is an answer the
    // table owes whoever comes looking.
    expect(sortKeys([key({ state: "revoked" })])).toHaveLength(1);
  });
});

describe("oneYearFromNow", () => {
  it("offers the same day a year later", () => {
    expect(oneYearFromNow(new Date("2026-09-19T12:00:00"))).toBe("2027-09-19");
  });

  it("gives a day, which is what a date field takes", () => {
    expect(oneYearFromNow()).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });
});

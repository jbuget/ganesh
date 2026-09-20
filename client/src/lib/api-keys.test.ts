import { describe, expect, it } from "vitest";

import { ApiKeyScope } from "@/lib/api/generated/model";
import type { ApiKeyResponse } from "@/lib/api/generated/model";
import {
  SCOPES,
  coveredBy,
  isUsable,
  oneYearFromNow,
  pruneCovered,
  scopeLabel,
  sortKeys,
} from "@/lib/api-keys";

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
    expect(scopeLabel("catalog:read")).toBe("Catalogue (lecture)");
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

describe("coveredBy", () => {
  it("leaves a precise scope alone when nothing broad is ticked", () => {
    expect(coveredBy("catalog:read", ["catalog:read"])).toBeNull();
  });

  it("says which broad scope already covers a read", () => {
    expect(coveredBy("catalog:read", ["all:read"])).toBe("all:read");
  });

  it("says which broad scope already covers a write", () => {
    expect(coveredBy("projects:write", ["all:write"])).toBe("all:write");
  });

  it("does not let one verb cover the other", () => {
    expect(coveredBy("projects:write", ["all:read"])).toBeNull();
    expect(coveredBy("catalog:read", ["all:write"])).toBeNull();
  });

  it("never lets one broad scope lock the other", () => {
    // Otherwise ticking « Tous (écriture) » would trap « Tous (lecture) »
    // checked and unremovable.
    expect(coveredBy("all:read", ["all:write"])).toBeNull();
    expect(coveredBy("all:write", ["all:read"])).toBeNull();
  });

  it("never reports a broad scope as covering itself", () => {
    expect(coveredBy("all:write", ["all:write"])).toBeNull();
    expect(coveredBy("all:read", ["all:read"])).toBeNull();
  });
});

describe("pruneCovered", () => {
  it("leaves precise scopes alone when none is broad", () => {
    expect(pruneCovered(["catalog:read", "projects:write"])).toEqual([
      "catalog:read",
      "projects:write",
    ]);
  });

  it("drops the reads « Tous (lecture) » already carries", () => {
    expect(pruneCovered(["all:read", "catalog:read", "entries:read"])).toEqual([
      "all:read",
    ]);
  });

  it("keeps a write beside « Tous (lecture) »", () => {
    expect(pruneCovered(["all:read", "projects:write"])).toEqual([
      "all:read",
      "projects:write",
    ]);
  });

  it("keeps both broad scopes when both were chosen", () => {
    expect(pruneCovered(["all:read", "all:write", "catalog:read"])).toEqual([
      "all:read",
      "all:write",
    ]);
  });
});

describe("the catalogue the form offers", () => {
  it("lists every scope the API knows, in its order", () => {
    // A scope the API carries and the form leaves out cannot be granted; one
    // the form carries and the API does not cannot be honoured. Neither is
    // something a reader of the table would ever find out.
    expect(SCOPES.map((scope) => scope.value)).toEqual(Object.values(ApiKeyScope));
  });

  it("says in French what each one opens", () => {
    for (const scope of SCOPES) {
      expect(scope.label).not.toBe("");
      expect(scope.hint).not.toBe("");
    }
  });
});

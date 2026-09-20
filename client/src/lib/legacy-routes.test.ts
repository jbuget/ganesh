import { describe, expect, it } from "vitest";

import { LEGACY_ROUTES } from "./legacy-routes";

describe("legacy routes", () => {
  it("sends the old timesheet address to the new one", () => {
    expect(LEGACY_ROUTES).toContainEqual({
      source: "/activite",
      destination: "/timesheet",
    });
  });

  it("never sends an address to one that is itself retired", () => {
    // A redirection onto a retired address would bounce, or worse, land on
    // whatever answers there next.
    const retired = new Set(LEGACY_ROUTES.map((route) => route.source));

    for (const { destination } of LEGACY_ROUTES) {
      expect(retired.has(destination)).toBe(false);
    }
  });

  it("retires each address once", () => {
    const sources = LEGACY_ROUTES.map((route) => route.source);

    expect(new Set(sources).size).toBe(sources.length);
  });
});

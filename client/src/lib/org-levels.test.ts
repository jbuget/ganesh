import { describe, expect, it } from "vitest";

import { ORG_LEVELS, orgLevelLabel } from "./org-levels";

describe("orgLevelLabel", () => {
  it("names the level as the company names it", () => {
    expect(orgLevelLabel("comex")).toBe("COMEX");
    expect(orgLevelLabel("comop")).toBe("COMOP");
    expect(orgLevelLabel("collaborator")).toBe("Collaborateur");
  });
});

describe("ORG_LEVELS", () => {
  it("offers the rungs from the top down", () => {
    expect(ORG_LEVELS.map((level) => level.value)).toEqual([
      "comex",
      "comop",
      "collaborator",
    ]);
  });
});

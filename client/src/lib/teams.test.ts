import { describe, expect, it } from "vitest";

import { keptTeam, teamLabel, teamsOf, workplaceLabel } from "./teams";

describe("teamsOf", () => {
  it("offers the three teams of the information systems, alphabetically", () => {
    expect(teamsOf("information_systems").map((team) => team.label)).toEqual([
      "Data",
      "Engineering",
      "Sysnet",
    ]);
  });

  it("offers nothing for a department nobody has cut into teams", () => {
    expect(teamsOf("customer_service")).toEqual([]);
  });

  it("offers nothing without a department", () => {
    expect(teamsOf(null)).toEqual([]);
  });
});

describe("teamLabel", () => {
  it("names the team as the department names it", () => {
    expect(teamLabel("sysnet")).toBe("Sysnet");
  });
});

describe("keptTeam", () => {
  it("keeps a team its department still holds", () => {
    expect(keptTeam("data", "information_systems")).toBe("data");
  });

  it("lets go of a team the new department does not hold", () => {
    expect(keptTeam("data", "landlords")).toBeNull();
  });

  it("lets go of a team once the department is emptied", () => {
    expect(keptTeam("data", null)).toBeNull();
  });
});

describe("workplaceLabel", () => {
  it("reads the team under its department", () => {
    expect(workplaceLabel("information_systems", "data")).toBe(
      "Système d'information · Data",
    );
  });

  it("reads the department alone when there is no team", () => {
    expect(workplaceLabel("landlords", null)).toBe("Bailleurs");
  });

  it("reads nothing when nobody has said", () => {
    expect(workplaceLabel(null, null)).toBeNull();
  });
});

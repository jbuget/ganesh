import { describe, expect, it } from "vitest";

import { ROLES, roleLabel } from "./roles";

describe("roleLabel", () => {
  it("names the role in French", () => {
    expect(roleLabel("MANAGER")).toBe("Manager");
    expect(roleLabel("TEAMMATE")).toBe("Collaborateur");
    expect(roleLabel("REQUESTER")).toBe("Demandeur");
  });
});

describe("ROLES", () => {
  it("lists the roles of the application, from the least to the most empowered", () => {
    expect(ROLES.map((role) => role.value)).toEqual([
      "REQUESTER",
      "TEAMMATE",
      "MANAGER",
    ]);
  });
});

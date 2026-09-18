import { describe, expect, it } from "vitest";

import { ROLES, roleLabel } from "./roles";

describe("libelleRole", () => {
  it("names the role in French", () => {
    expect(roleLabel("MANAGER")).toBe("Manager");
    expect(roleLabel("TEAMMATE")).toBe("Collaborateur");
  });
});

describe("ROLES", () => {
  it("lists the two roles of the application", () => {
    expect(ROLES.map((role) => role.value)).toEqual(["TEAMMATE", "MANAGER"]);
  });
});

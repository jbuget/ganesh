import { describe, expect, it } from "vitest";

import { ROLES, libelleRole } from "./roles";

describe("libelleRole", () => {
  it("names the role in French", () => {
    expect(libelleRole("MANAGER")).toBe("Manager");
    expect(libelleRole("TEAMMATE")).toBe("Collaborateur");
  });
});

describe("ROLES", () => {
  it("lists the two roles of the application", () => {
    expect(ROLES.map((role) => role.value)).toEqual(["TEAMMATE", "MANAGER"]);
  });
});

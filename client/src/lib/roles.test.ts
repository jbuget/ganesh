import { describe, expect, it } from "vitest";

import { ROLES, libelleRole } from "./roles";

describe("libelleRole", () => {
  it("nomme le rôle en français", () => {
    expect(libelleRole("MANAGER")).toBe("Manager");
    expect(libelleRole("TEAMMATE")).toBe("Collaborateur");
  });
});

describe("ROLES", () => {
  it("énumère les deux rôles de l'application", () => {
    expect(ROLES.map((role) => role.value)).toEqual(["TEAMMATE", "MANAGER"]);
  });
});

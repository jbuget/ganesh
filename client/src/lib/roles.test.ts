import { describe, expect, it } from "vitest";

import { ROLES, grantableBy, isManager, mayActOn, roleLabel } from "./roles";

describe("roleLabel", () => {
  it("names the role in French", () => {
    expect(roleLabel("ADMIN")).toBe("Administrateur");
    expect(roleLabel("MANAGER")).toBe("Manager");
    expect(roleLabel("TEAMMATE")).toBe("Collaborateur");
    expect(roleLabel("GUEST")).toBe("Invité");
  });
});

describe("ROLES", () => {
  it("lists the roles of the application, from the least to the most empowered", () => {
    expect(ROLES.map((role) => role.value)).toEqual([
      "GUEST",
      "TEAMMATE",
      "MANAGER",
      "ADMIN",
    ]);
  });
});

describe("isManager", () => {
  it("counts the admin above, who would otherwise be the weaker of the two", () => {
    expect(isManager({ role: "ADMIN" })).toBe(true);
    expect(isManager({ role: "MANAGER" })).toBe(true);
    expect(isManager({ role: "TEAMMATE" })).toBe(false);
    expect(isManager({ role: "GUEST" })).toBe(false);
    expect(isManager(undefined)).toBe(false);
  });
});

describe("grantableBy", () => {
  it("stops at the rank one holds oneself", () => {
    expect(grantableBy({ role: "MANAGER" })).toEqual(["GUEST", "TEAMMATE", "MANAGER"]);
    expect(grantableBy({ role: "ADMIN" })).toEqual([
      "GUEST",
      "TEAMMATE",
      "MANAGER",
      "ADMIN",
    ]);
  });

  it("hands nothing to whoever manages nobody", () => {
    expect(grantableBy({ role: "TEAMMATE" })).toEqual([]);
  });
});

describe("mayActOn", () => {
  const admin = { id: 1, role: "ADMIN" } as const;
  const manager = { id: 2, role: "MANAGER" } as const;
  const teammate = { id: 3, role: "TEAMMATE" } as const;

  it("lets a manager move whoever stands below or beside them", () => {
    expect(mayActOn(manager, teammate)).toBe(true);
    expect(mayActOn(manager, { id: 4, role: "MANAGER" })).toBe(true);
  });

  it("stops a manager at the rank above", () => {
    expect(mayActOn(manager, admin)).toBe(false);
  });

  it("stops anybody at their own account", () => {
    expect(mayActOn(admin, admin)).toBe(false);
  });

  it("stops whoever manages nobody", () => {
    expect(mayActOn(teammate, manager)).toBe(false);
  });
});

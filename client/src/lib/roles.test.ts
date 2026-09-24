import { describe, expect, it } from "vitest";

import { assignableRoles, canWrite, holds, roleLabel } from "@/lib/roles";

describe("roleLabel", () => {
  it("names every rung of the ladder in French", () => {
    expect(roleLabel("GUEST")).toBe("Invité");
    expect(roleLabel("TEAMMATE")).toBe("Collaborateur");
    expect(roleLabel("MANAGER")).toBe("Manager");
    expect(roleLabel("ADMIN")).toBe("Administrateur");
  });
});

describe("canWrite", () => {
  it("lets anybody but a guest write", () => {
    expect(canWrite("TEAMMATE")).toBe(true);
    expect(canWrite("MANAGER")).toBe(true);
    expect(canWrite("ADMIN")).toBe(true);
  });

  it("turns a guest back", () => {
    expect(canWrite("GUEST")).toBe(false);
  });

  it("turns back a role nobody has read yet", () => {
    expect(canWrite(undefined)).toBe(false);
  });
});

describe("holds", () => {
  it("reads the ladder upwards", () => {
    expect(holds("ADMIN", "MANAGER")).toBe(true);
    expect(holds("MANAGER", "MANAGER")).toBe(true);
    expect(holds("TEAMMATE", "MANAGER")).toBe(false);
  });
});

describe("assignableRoles", () => {
  const admin = { id: 1, role: "ADMIN" as const };
  const manager = { id: 2, role: "MANAGER" as const };
  const teammate = { id: 3, role: "TEAMMATE" as const };

  it("hands an admin every role", () => {
    expect(assignableRoles(admin, teammate)).toEqual([
      "GUEST",
      "TEAMMATE",
      "MANAGER",
      "ADMIN",
    ]);
  });

  it("stops a manager at their own rung", () => {
    expect(assignableRoles(manager, teammate)).toEqual([
      "GUEST",
      "TEAMMATE",
      "MANAGER",
    ]);
  });

  it("leaves an admin alone when a manager reads the row", () => {
    expect(assignableRoles(manager, admin)).toEqual([]);
  });

  it("offers nothing below a manager", () => {
    expect(assignableRoles(teammate, teammate)).toEqual([]);
    expect(assignableRoles({ id: 4, role: "GUEST" }, teammate)).toEqual([]);
  });

  it("offers nobody their own row", () => {
    expect(assignableRoles(admin, admin)).toEqual([]);
  });

  it("offers nothing while the current user is still unknown", () => {
    expect(assignableRoles(undefined, teammate)).toEqual([]);
  });
});

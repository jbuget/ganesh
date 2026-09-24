import { describe, expect, it } from "vitest";

import { SCREENS, screensFor } from "@/lib/navigation";

const hrefs = (role: Parameters<typeof screensFor>[0]) =>
  screensFor(role).map((screen) => screen.href);

describe("screensFor", () => {
  it("shows every working screen to a guest", () => {
    // The navigation says what exists, and the permission lives on the
    // actions: a guest reads the application whole.
    expect(hrefs("GUEST")).toContain("/timesheet");
    expect(hrefs("GUEST")).toContain("/users");
    expect(hrefs("GUEST")).toContain("/api-mcp");
  });

  it("keeps the administration out of everyone's way but an admin's", () => {
    expect(hrefs("GUEST")).not.toContain("/admin");
    expect(hrefs("TEAMMATE")).not.toContain("/admin");
    expect(hrefs("MANAGER")).not.toContain("/admin");
    expect(hrefs("ADMIN")).toContain("/admin");
  });

  it("shows nothing reserved while the reader is still unknown", () => {
    expect(hrefs(undefined)).not.toContain("/admin");
  });

  it("is the whole list for an admin", () => {
    expect(screensFor("ADMIN")).toHaveLength(SCREENS.length);
  });
});

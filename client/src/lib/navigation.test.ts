import { describe, expect, it } from "vitest";

import { SCREENS, bandsFor, screensFor } from "@/lib/navigation";

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

describe("bandsFor", () => {
  const bands = (role: Parameters<typeof bandsFor>[0]) =>
    bandsFor(role).map((band) => band.band);

  it("opens on what one does every morning, under no heading", () => {
    const first = bandsFor("MANAGER")[0];

    expect(first.band).toBe("work");
    expect(first.label).toBeNull();
    expect(first.screens.map((screen) => screen.href)).toEqual(["/", "/timesheet"]);
  });

  it("names every other band", () => {
    for (const band of bandsFor("ADMIN").slice(1)) {
      expect(band.label).not.toBeNull();
    }
  });

  it("holds the bands in the order the screens are read in", () => {
    expect(bands("ADMIN")).toEqual([
      "work",
      "portfolio",
      "steering",
      "team",
      "platform",
    ]);
  });

  it("keeps a screen out of the bar without taking it out of the application", () => {
    const listed = bandsFor("ADMIN").flatMap((band) =>
      band.screens.map((screen) => screen.href),
    );

    // Read from where it belongs — the home screen — rather than listed every
    // day beside screens one opens hourly. The palette still leads to it.
    expect(listed).not.toContain("/gazette");
    expect(hrefs("ADMIN")).toContain("/gazette");
  });

  it("opens the team band on the mirror, before the list", () => {
    const team = bandsFor("MANAGER").find((band) => band.band === "team");

    // How the team is, and then who it is made of.
    expect(team?.screens.map((screen) => screen.href)).toEqual(["/mood", "/users"]);
  });

  it("shows the administration to nobody else, in the band that holds it", () => {
    const platform = (role: Parameters<typeof bandsFor>[0]) =>
      bandsFor(role)
        .find((band) => band.band === "platform")
        ?.screens.map((screen) => screen.href);

    expect(platform("MANAGER")).toEqual(["/logs", "/stats", "/api-mcp"]);
    expect(platform("ADMIN")).toEqual(["/logs", "/stats", "/api-mcp", "/admin"]);
  });
});

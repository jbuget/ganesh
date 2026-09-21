import { describe, expect, it } from "vitest";

import type { Surface } from "@/lib/api/generated/model";
import {
  formatLastUse,
  formatPeopleDelta,
  summariseIdle,
  surfaceLabel,
} from "@/lib/surfaces";

/** Every function the API can name. Adding one here without a wording fails. */
const SURFACES: Surface[] = [
  "time_entry",
  "month_closing",
  "project_registry",
  "phase_progress",
  "assignment",
  "project_updates",
  "planning",
  "gazette",
  "mood",
  "notifications",
  "team_admin",
  "api_keys",
  "machine_access",
];

describe("surfaceLabel", () => {
  it("names every function in French", () => {
    // A line the interface cannot name would show its domain key to the
    // whole team.
    for (const surface of SURFACES) {
      expect(surfaceLabel(surface)).not.toBe(surface);
    }
  });

  it("names a function after the gesture rather than the screen", () => {
    // The same gesture comes from the board and from the sheet: naming the
    // line « Kanban » would make one of the two doors invisible.
    expect(surfaceLabel("phase_progress")).toBe("Avancement des phases");
  });

  it("says « projet » rather than « mission »", () => {
    expect(surfaceLabel("project_registry")).toContain("projets");
  });
});

describe("formatPeopleDelta", () => {
  it("shows a gain with its sign", () => {
    expect(formatPeopleDelta(2)).toBe("+2");
  });

  it("shows a loss with a true minus sign", () => {
    expect(formatPeopleDelta(-3)).toBe("−3");
  });

  it("says a count held rather than showing nothing", () => {
    // An em dash would read as « no figure », where the figure is that it
    // did not move.
    expect(formatPeopleDelta(0)).toBe("=");
  });
});

describe("formatLastUse", () => {
  it("dates the last time somebody used it", () => {
    expect(formatLastUse("2026-06-04")).toBe("4 juin 2026");
  });

  it("says « jamais » rather than leaving a blank", () => {
    expect(formatLastUse(null)).toBe("jamais");
  });
});

describe("summariseIdle", () => {
  it("counts what served nobody", () => {
    expect(summariseIdle(3)).toBe("3 fonctions n'ont servi à personne sur la période.");
  });

  it("agrees in the singular", () => {
    expect(summariseIdle(1)).toBe("1 fonction n'a servi à personne sur la période.");
  });

  it("says so when everything served", () => {
    expect(summariseIdle(0)).toBe("Toutes les fonctions ont servi sur la période.");
  });
});

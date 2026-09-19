import { describe, expect, it } from "vitest";

import {
  RANGES,
  categoryRows,
  kindRows,
  missionRows,
  phaseRows,
  formatDelay,
  formatPersonDays,
  formatPoints,
  formatShare,
  rangeLabel,
  summarise,
} from "./statistics";

describe("rangeLabel", () => {
  it("names every window the screen offers", () => {
    expect(RANGES.map((range) => range.value)).toEqual([
      "today",
      "yesterday",
      "last_7_days",
      "last_30_days",
      "last_90_days",
    ]);
  });

  it("names a window in plain French", () => {
    expect(rangeLabel("last_30_days")).toBe("30 derniers jours");
  });
});

describe("formatShare", () => {
  it("reads a share as a whole percentage", () => {
    expect(formatShare(0.87)).toBe("87 %");
  });

  it("rounds to the nearest point", () => {
    expect(formatShare(0.874)).toBe("87 %");
    expect(formatShare(0.876)).toBe("88 %");
  });

  it("says nothing rather than zero when there is nothing to read", () => {
    // A weekend expects nothing: « 0 % » would read as a failure that is not
    // one.
    expect(formatShare(null)).toBe("—");
  });

  it("reports an excess as it stands", () => {
    expect(formatShare(1.125)).toBe("113 %");
  });
});

describe("formatPoints", () => {
  it("signs a rise", () => {
    expect(formatPoints(6)).toBe("+6 pts");
  });

  it("signs a fall", () => {
    expect(formatPoints(-4.2)).toBe("−4,2 pts");
  });

  it("drops the decimal when there is none", () => {
    expect(formatPoints(6.0)).toBe("+6 pts");
  });

  it("says nothing without a period to compare against", () => {
    expect(formatPoints(null)).toBe("—");
  });

  it("uses the singular for a single point", () => {
    expect(formatPoints(1)).toBe("+1 pt");
  });
});

describe("formatPersonDays", () => {
  it("counts person-days with the French decimal comma", () => {
    expect(formatPersonDays(142.5)).toBe("142,5");
  });

  it("drops a trailing zero", () => {
    expect(formatPersonDays(142)).toBe("142");
  });
});

describe("formatDelay", () => {
  it("tells a delay in days", () => {
    expect(formatDelay(1.5)).toBe("1,5 j");
  });

  it("names the same day rather than counting zero days", () => {
    expect(formatDelay(0)).toBe("le jour même");
  });

  it("says nothing when no entry was written", () => {
    expect(formatDelay(null)).toBe("—");
  });
});

describe("summarise", () => {
  it("reads a window as a span of dates and its working days", () => {
    expect(
      summarise({
        range: "last_7_days",
        start: "2026-09-11",
        end: "2026-09-17",
        working_days: 5,
      }),
    ).toBe("Du 11 au 17 septembre 2026 · 5 jours ouvrés");
  });

  it("names both months when the window straddles them", () => {
    expect(
      summarise({
        range: "last_30_days",
        start: "2026-08-19",
        end: "2026-09-17",
        working_days: 22,
      }),
    ).toBe("Du 19 août au 17 septembre 2026 · 22 jours ouvrés");
  });

  it("names both years when the window straddles them", () => {
    expect(
      summarise({
        range: "last_90_days",
        start: "2025-12-20",
        end: "2026-03-19",
        working_days: 62,
      }),
    ).toBe("Du 20 décembre 2025 au 19 mars 2026 · 62 jours ouvrés");
  });

  it("names a single day on its own", () => {
    expect(
      summarise({
        range: "today",
        start: "2026-09-17",
        end: "2026-09-17",
        working_days: 1,
      }),
    ).toBe("Le 17 septembre 2026 · 1 jour ouvré");
  });

  it("says plainly when a window expects nothing", () => {
    expect(
      summarise({
        range: "today",
        start: "2026-09-20",
        end: "2026-09-20",
        working_days: 0,
      }),
    ).toBe("Le 20 septembre 2026 · aucun jour ouvré");
  });
});

describe("breakdown rows", () => {
  const steering = {
    project_days: 18,
    off_project_days: 2,
    project_share: 0.9,
    by_status: [
      { status: "development" as const, days: 12, share: 0.6 },
      { status: "scoping" as const, days: 6, share: 0.3 },
    ],
    by_category: [
      { category: "automate_streamline" as const, days: 12, share: 0.6 },
      { category: null, days: 8, share: 0.4 },
    ],
    top_missions: [{ project_id: 7, label: "Extranet", days: 12, share: 0.6 }],
  };

  it("names each phase the way the kanban does", () => {
    expect(phaseRows(steering).map((row) => row.label)).toEqual([
      "Réalisation",
      "Cadrage",
    ]);
  });

  it("keeps the colour a phase carries on the board", () => {
    // The same phase must be recognisable from one screen to the next.
    expect(phaseRows(steering)[0].colour).toBe("bg-blue-500");
  });

  it("names each strategic axis", () => {
    expect(categoryRows(steering)[0].label).toBe("Automatiser & fluidifier");
  });

  it("names what carries no axis rather than leaving it blank", () => {
    expect(categoryRows(steering)[1].label).toBe("Sans axe");
  });

  it("lists the heaviest missions with their own label", () => {
    expect(missionRows(steering)).toEqual([
      { key: "7", label: "Extranet", days: 12, share: 0.6 },
    ]);
  });

  it("splits the time between missions and what surrounds them", () => {
    expect(kindRows(steering)).toEqual([
      { key: "project", label: "Sur mission", days: 18, share: 0.9 },
      {
        key: "off_project",
        label: "Hors projet",
        days: 2,
        share: 0.1,
        colour: "bg-slate-300",
      },
    ]);
  });

  it("reads no share out of a period where nothing was declared", () => {
    const empty = {
      ...steering,
      project_days: 0,
      off_project_days: 0,
      project_share: null,
    };

    expect(kindRows(empty).map((row) => row.share)).toEqual([null, null]);
  });
});

import { describe, expect, it } from "vitest";

import type { RoadmapMissionResponse } from "@/lib/api/generated/model";
import {
  bandsOf,
  dayAfter,
  daysBetween,
  groupingLabel,
  monthsOf,
  silentNotice,
  speaks,
  placeOn,
  positionOf,
  roadmapNotice,
} from "@/lib/roadmap";

const FROM = "2026-01-01";
const TO = "2026-12-31";

function aLine(fields: Partial<RoadmapMissionResponse> = {}): RoadmapMissionResponse {
  return {
    project_id: 1,
    label: "Portail",
    kind: "project",
    status: "development",
    priority: null,
    category: null,
    parent_id: null,
    segments: [],
    target_date: null,
    landing_date: null,
    slippage_days: null,
    is_late: false,
    estimated_days: null,
    consumed_days: 0,
    remaining_days: null,
    blocker: null,
    is_active: true,
    ...fields,
  };
}

describe("counting days", () => {
  it("counts the days between two ISO days", () => {
    expect(daysBetween("2026-01-01", "2026-01-31")).toBe(30);
  });

  it("crosses a month boundary without drifting", () => {
    expect(daysBetween("2026-02-28", "2026-03-01")).toBe(1);
  });

  it("names the day after one", () => {
    expect(dayAfter("2026-12-31", 1)).toBe("2027-01-01");
  });
});

describe("placing a day on the axis", () => {
  it("puts the first day of the window at the very start", () => {
    expect(positionOf(FROM, FROM, TO)).toBe(0);
  });

  it("puts the middle of the year near the middle", () => {
    expect(positionOf("2026-07-02", FROM, TO)).toBeCloseTo(0.5, 2);
  });
});

describe("placing a stretch of days", () => {
  it("leaves out a stretch that misses the window entirely", () => {
    expect(placeOn("2024-01-01", "2024-06-01", FROM, TO)).toBeNull();
  });

  it("gives a single day a width one can see", () => {
    const placed = placeOn("2026-06-01", "2026-06-01", FROM, TO);

    expect(placed?.width).toBeGreaterThan(0);
  });

  it("cuts a stretch reaching in from before, and says so", () => {
    const placed = placeOn("2025-10-01", "2026-03-01", FROM, TO);

    expect(placed?.left).toBe(0);
    expect(placed?.clippedLeft).toBe(true);
    expect(placed?.clippedRight).toBe(false);
  });

  it("cuts a stretch running past the end, and says so", () => {
    const placed = placeOn("2026-10-01", "2027-06-01", FROM, TO);

    expect(placed?.clippedRight).toBe(true);
    expect((placed?.left ?? 0) + (placed?.width ?? 0)).toBeCloseTo(1, 5);
  });
});

describe("the scale of months", () => {
  it("names every month of the window", () => {
    expect(monthsOf(FROM, TO)).toHaveLength(12);
  });

  it("gives each month its real width, not an equal share", () => {
    const [january, february] = monthsOf(FROM, TO);

    expect(january.width).toBeGreaterThan(february.width);
  });

  it("covers the whole width and no more", () => {
    const total = monthsOf(FROM, TO).reduce((sum, tick) => sum + tick.width, 0);

    expect(total).toBeCloseTo(1, 5);
  });

  it("names the grouping in force", () => {
    expect(groupingLabel("category")).toBe("Par axe stratégique");
  });

  it("handles a window opening mid-month", () => {
    const ticks = monthsOf("2026-09-15", "2026-10-31");

    expect(ticks.map((tick) => tick.label)).toEqual(["sept.", "oct."]);
    expect(ticks[0].width).toBeLessThan(ticks[1].width);
  });
});

describe("gathering lines into bands", () => {
  it("reads axes in the order the rest of the application does", () => {
    const bands = bandsOf(
      [
        aLine({ project_id: 1, category: "structure_platform" }),
        aLine({ project_id: 2, category: "automate_streamline" }),
      ],
      "category",
    );

    expect(bands.map((band) => band.label)).toEqual([
      "Automatiser & fluidifier",
      "Structurer la plateforme",
    ]);
  });

  it("puts what carries no axis last", () => {
    const bands = bandsOf(
      [aLine({ project_id: 1 }), aLine({ project_id: 2, category: "sustain_growth" })],
      "category",
    );

    expect(bands.map((band) => band.label)).toEqual([
      "Pérenniser la croissance",
      "Sans axe",
    ]);
  });

  it("drops the bands nothing falls into", () => {
    const bands = bandsOf([aLine({ category: "sustain_growth" })], "category");

    expect(bands).toHaveLength(1);
  });

  it("gathers everything under one band when asked for none", () => {
    const bands = bandsOf([aLine({ project_id: 1 }), aLine({ project_id: 2 })], "none");

    expect(bands).toHaveLength(1);
    expect(bands[0].missions).toHaveLength(2);
  });

  it("groups by phase in column order", () => {
    const bands = bandsOf(
      [
        aLine({ project_id: 1, status: "operations" }),
        aLine({ project_id: 2, status: "scoping" }),
      ],
      "status",
    );

    expect(bands.map((band) => band.label)).toEqual(["Cadrage", "Exploitation"]);
  });
});

describe("telling a line that speaks from one that does not", () => {
  it("a bar is enough to speak", () => {
    expect(
      speaks(
        aLine({
          segments: [
            {
              kind: "lived",
              status: "development",
              starts_on: "2026-03-02",
              ends_on: "2026-09-18",
            },
          ],
        }),
      ),
    ).toBe(true);
  });

  it("a date on its own is enough: the diamond sits on the axis", () => {
    expect(speaks(aLine({ target_date: "2026-11-30" }))).toBe(true);
  });

  it("neither one nor the other and the line says nothing", () => {
    expect(speaks(aLine())).toBe(false);
  });

  it("a band keeps its silent lines apart without losing them", () => {
    const [band] = bandsOf(
      [
        aLine({ project_id: 1, target_date: "2026-11-30" }),
        aLine({ project_id: 2 }),
        aLine({ project_id: 3 }),
      ],
      "none",
    );

    expect(band.speaking).toHaveLength(1);
    expect(band.silent).toHaveLength(2);
    expect(band.missions).toHaveLength(3);
  });

  it("counts what is folded away, in words", () => {
    expect(silentNotice(1)).toBe("1 mission sans rien à montrer");
    expect(silentNotice(12)).toBe("12 missions sans rien à montrer");
  });
});

describe("what the drawing is worth", () => {
  it("says only the count when nothing is missing", () => {
    const notice = roadmapNotice({
      missions: 1,
      late: 0,
      undated: 0,
      unestimated: 0,
      delivered: 0,
    });

    expect(notice).toBe("1 mission");
  });

  it("names what is missing before the drawing can be believed", () => {
    const notice = roadmapNotice({
      missions: 14,
      late: 3,
      undated: 5,
      unestimated: 2,
      delivered: 4,
    });

    expect(notice).toBe(
      "14 missions · 4 livrées · 3 en retard · 5 sans date · 2 sans estimation",
    );
  });
});

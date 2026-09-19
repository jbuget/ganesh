import { describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { RoadmapTimeline } from "./RoadmapTimeline";
import type {
  RoadmapMissionResponse,
  RoadmapSegmentResponse,
} from "@/lib/api/generated/model";

const FROM = "2026-01-01";
const TO = "2026-12-31";
const TODAY = "2026-09-18";

function aLine(
  overrides: Partial<RoadmapMissionResponse> = {},
): RoadmapMissionResponse {
  return {
    project_id: 1,
    label: "Portail bailleurs",
    kind: "project",
    status: "development",
    priority: null,
    category: "innovate_differentiate",
    parent_id: null,
    segments: [],
    target_date: null,
    went_live_on: null,
    landing_date: null,
    slippage_days: null,
    is_late: false,
    estimated_days: 8,
    consumed_days: 3,
    remaining_days: 5,
    blocker: null,
    is_active: true,
    ...overrides,
  };
}

function lived(startsOn: string, endsOn: string): RoadmapSegmentResponse {
  return { kind: "lived", status: "development", starts_on: startsOn, ends_on: endsOn };
}

function draw(
  missions: RoadmapMissionResponse[],
  handlers: { onOpen?: () => void; onDate?: () => void } = {},
) {
  const onOpen = handlers.onOpen ?? vi.fn();
  const onDate = handlers.onDate ?? vi.fn();
  render(
    <RoadmapTimeline
      missions={missions}
      from={FROM}
      to={TO}
      today={TODAY}
      grouping="category"
      onOpen={onOpen}
      onDate={onDate}
    />,
  );
  return { onOpen, onDate };
}

describe("RoadmapTimeline", () => {
  it("names the months the window spans", () => {
    draw([aLine()]);

    expect(screen.getByText("janv.")).toBeInTheDocument();
    expect(screen.getByText("déc.")).toBeInTheDocument();
  });

  it("gathers the missions under the band of their axis", () => {
    draw([aLine()]);

    expect(screen.getByText("Innover & différencier")).toBeInTheDocument();
  });

  it("says when there is nothing to show rather than drawing an empty frame", () => {
    draw([]);

    expect(
      screen.getByText("Aucun projet à montrer sur cette période."),
    ).toBeInTheDocument();
  });

  it("opens the mission beside the drawing when its line is clicked", async () => {
    const onOpen = vi.fn();
    draw([aLine({ segments: [lived("2026-03-02", TODAY)] })], { onOpen });

    await userEvent.click(
      screen.getByRole("button", { name: "Ouvrir Portail bailleurs" }),
    );

    expect(onOpen).toHaveBeenCalledWith(1);
  });

  it("does not open the mission when the date is what was aimed at", async () => {
    // Posting a commitment is an act of its own: it must not be swallowed by
    // the row underneath it.
    const onOpen = vi.fn();
    draw([aLine({ segments: [lived("2026-03-02", TODAY)] })], { onOpen });

    await userEvent.click(
      screen.getByRole("button", { name: /Date annoncée pour Portail bailleurs/ }),
    );

    expect(onOpen).not.toHaveBeenCalled();
  });

  it("tells what was lived from what is supposed", () => {
    draw([
      aLine({
        segments: [
          lived("2026-03-02", TODAY),
          {
            kind: "projected",
            status: "development",
            starts_on: "2026-09-19",
            ends_on: "2026-11-20",
          },
        ],
      }),
    ]);

    expect(screen.getByTitle(/^Vécu · /)).toBeInTheDocument();
    expect(screen.getByTitle(/^Projeté · /)).toBeInTheDocument();
  });

  it("marks the date a mission was announced for", () => {
    draw([aLine({ target_date: "2026-11-30" })]);

    expect(screen.getByTitle("Date annoncée : 2026-11-30")).toBeInTheDocument();
  });

  it("says how late a mission is, in words", () => {
    draw([
      aLine({
        target_date: "2026-10-01",
        landing_date: "2026-11-05",
        slippage_days: 35,
        is_late: true,
      }),
    ]);

    expect(screen.getByText("35 jours de retard")).toBeInTheDocument();
  });

  it("says why a mission has no bar, once its line is opened", async () => {
    draw([aLine({ blocker: "no_estimate", estimated_days: null })]);

    await userEvent.click(screen.getByRole("button", { name: /sans rien à montrer/ }));

    expect(screen.getByText("Sans estimation")).toBeInTheDocument();
  });

  it("folds away the lines with nothing to show, and counts them", () => {
    draw([
      aLine({ project_id: 1, segments: [lived("2026-03-02", TODAY)] }),
      aLine({ project_id: 2, label: "Sans rien", blocker: "no_estimate" }),
      aLine({ project_id: 3, label: "Sans rien non plus", blocker: "no_assignee" }),
    ]);

    expect(screen.getByText("2 projets sans rien à montrer")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Ouvrir Sans rien" }),
    ).not.toBeInTheDocument();
  });

  it("opens them when asked", async () => {
    draw([
      aLine({ project_id: 1, segments: [lived("2026-03-02", TODAY)] }),
      aLine({ project_id: 2, label: "Sans rien", blocker: "no_estimate" }),
    ]);

    await userEvent.click(
      screen.getByRole("button", { name: /1 projet sans rien à montrer/ }),
    );

    expect(
      screen.getByRole("button", { name: "Ouvrir Sans rien" }),
    ).toBeInTheDocument();
  });

  it("leaves a dated mission in plain sight, bar or no bar", () => {
    // Its diamond sits on the axis and can be read against the others.
    draw([aLine({ label: "Promise", target_date: "2026-11-30" })]);

    expect(screen.getByRole("button", { name: "Ouvrir Promise" })).toBeInTheDocument();
    expect(screen.queryByText(/sans rien à montrer/)).not.toBeInTheDocument();
  });

  it("counts the missions of each band", () => {
    draw([aLine({ project_id: 1 }), aLine({ project_id: 2, label: "Socle" })]);

    const band = screen.getByRole("heading", { name: /Innover & différencier/ });
    expect(within(band).getByText("2")).toBeInTheDocument();
  });
});

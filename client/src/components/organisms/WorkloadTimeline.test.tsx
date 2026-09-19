import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { WorkloadTimeline } from "./WorkloadTimeline";
import type { PlannedMissionResponse } from "@/lib/api/generated/model";

const WEEKS = ["2026-09-14", "2026-09-21", "2026-10-05"];

function aMission(
  overrides: Partial<PlannedMissionResponse> = {},
): PlannedMissionResponse {
  return {
    project_id: 10,
    label: "Portail bailleurs",
    kind: "project",
    status: "development",
    priority: "high",
    parent_id: null,
    estimated_days: 20,
    remaining_days: 7,
    scheduled_days: 7,
    starts_on: "2026-09-14",
    ends_on: "2026-09-22",
    target_date: null,
    slippage_days: null,
    blocker: null,
    assignees: [],
    weeks: [
      { week: "2026-09-14", days: 5 },
      { week: "2026-09-21", days: 2 },
    ],
    ...overrides,
  };
}

describe("WorkloadTimeline", () => {
  it("lines the weeks of the horizon up as columns", () => {
    render(<WorkloadTimeline missions={[aMission()]} weeks={WEEKS} onMove={vi.fn()} />);

    expect(screen.getByText("14 sept.")).toBeInTheDocument();
    expect(screen.getByText("5 oct.")).toBeInTheDocument();
  });

  it("names the month again on the week that opens it", () => {
    // Twenty-six columns of « 14 sept. » and one no longer knows what year,
    // let alone what quarter, one is reading.
    render(<WorkloadTimeline missions={[aMission()]} weeks={WEEKS} onMove={vi.fn()} />);

    expect(screen.getByText("septembre 2026")).toBeInTheDocument();
    expect(screen.getByText("octobre 2026")).toBeInTheDocument();
  });

  it("draws the span a mission occupies across the weeks", () => {
    render(<WorkloadTimeline missions={[aMission()]} weeks={WEEKS} onMove={vi.fn()} />);

    expect(screen.getByTitle("5 j cette semaine")).toBeInTheDocument();
    expect(screen.getByTitle("2 j cette semaine")).toBeInTheDocument();
  });

  it("draws the missions in the order they are served", () => {
    render(
      <WorkloadTimeline
        missions={[aMission(), aMission({ project_id: 20, label: "Facturation" })]}
        weeks={WEEKS}
        onMove={vi.fn()}
      />,
    );

    const drawn = screen
      .getAllByRole("button", { name: /^Déplacer / })
      .map((handle) => handle.getAttribute("aria-label"));

    expect(drawn).toEqual(["Déplacer Portail bailleurs", "Déplacer Facturation"]);
  });

  it("offers to move every mission", () => {
    render(<WorkloadTimeline missions={[aMission()]} weeks={WEEKS} onMove={vi.fn()} />);

    expect(
      screen.getByRole("button", { name: "Déplacer Portail bailleurs" }),
    ).toBeInTheDocument();
  });

  it("says why a mission carries no date instead of leaving it blank", () => {
    render(
      <WorkloadTimeline
        missions={[
          aMission({ blocker: "no_estimate", ends_on: null, remaining_days: 0 }),
        ]}
        weeks={WEEKS}
        onMove={vi.fn()}
      />,
    );

    expect(screen.getByText("Sans estimation")).toBeInTheDocument();
    expect(
      screen.getByTitle("Estimez le build pour la placer dans le plan"),
    ).toBeInTheDocument();
  });

  it("announces an empty backlog in its own words", () => {
    render(<WorkloadTimeline missions={[]} weeks={WEEKS} onMove={vi.fn()} />);

    expect(screen.getByText(/Aucune mission à planifier/)).toBeInTheDocument();
  });
});

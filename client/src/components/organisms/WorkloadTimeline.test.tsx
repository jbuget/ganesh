import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { WorkloadTimeline } from "./WorkloadTimeline";
import type {
  PlanMemberResponse,
  PlannedMissionResponse,
} from "@/lib/api/generated/model";

const WEEKS = ["2026-09-14", "2026-09-21", "2026-10-05"];

const TEAM: PlanMemberResponse[] = [
  { id: 1, display_name: "Alice Martin", initials: "AM" },
  { id: 2, display_name: "Bob Durand", initials: "BD" },
];

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
    is_late: false,
    blocker: null,
    assignees: [],
    weeks: [
      { week: "2026-09-14", days: 5 },
      { week: "2026-09-21", days: 2 },
    ],
    ...overrides,
  };
}

const NOTHING = {
  onMove: vi.fn(),
  onTop: vi.fn(),
  onUp: vi.fn(),
  onDown: vi.fn(),
  onStaff: vi.fn(),
};

function draw(missions: PlannedMissionResponse[], handlers = {}) {
  return render(
    <WorkloadTimeline
      missions={missions}
      weeks={WEEKS}
      team={TEAM}
      {...NOTHING}
      {...handlers}
    />,
  );
}

describe("WorkloadTimeline", () => {
  it("lines the weeks of the horizon up as columns", () => {
    draw([aMission()]);

    expect(screen.getByText("14 sept.")).toBeInTheDocument();
    expect(screen.getByText("5 oct.")).toBeInTheDocument();
  });

  it("names the month again on the week that opens it", () => {
    // Twenty-six columns of « 14 sept. » and one no longer knows what year,
    // let alone what quarter, one is reading.
    draw([aMission()]);

    expect(screen.getByText("septembre 2026")).toBeInTheDocument();
    expect(screen.getByText("octobre 2026")).toBeInTheDocument();
  });

  it("draws the span a mission occupies across the weeks", () => {
    draw([aMission()]);

    expect(screen.getByTitle("5 j cette semaine")).toBeInTheDocument();
    expect(screen.getByTitle("2 j cette semaine")).toBeInTheDocument();
  });

  it("draws the missions in the order they are served", () => {
    draw([aMission(), aMission({ project_id: 20, label: "Facturation" })]);

    const drawn = screen
      .getAllByRole("button", { name: /^Déplacer / })
      .map((handle) => handle.getAttribute("aria-label"));

    expect(drawn).toEqual(["Déplacer Portail bailleurs", "Déplacer Facturation"]);
  });

  it("offers every lever on every row, without having to hover", () => {
    // The first complaint the screen drew: a grip handle announces nothing,
    // and a tool one cannot see is a tool nobody uses.
    draw([aMission(), aMission({ project_id: 20, label: "Facturation" })]);

    for (const name of [
      "Passer Facturation en tête",
      "Monter Facturation",
      "Descendre Portail bailleurs",
      "Changer les intervenants de Portail bailleurs",
    ]) {
      expect(screen.getByRole("button", { name })).toBeInTheDocument();
    }
  });

  it("sends a mission straight to the front", async () => {
    // Forty ranks one row at a time is a chore, not an arbitration.
    const onTop = vi.fn();
    draw([aMission(), aMission({ project_id: 20, label: "Facturation" })], { onTop });

    await userEvent.click(
      screen.getByRole("button", { name: "Passer Facturation en tête" }),
    );

    expect(onTop).toHaveBeenCalledWith(20);
  });

  it("does not offer to raise what already leads, nor to lower what trails", () => {
    draw([aMission(), aMission({ project_id: 20, label: "Facturation" })]);

    expect(
      screen.getByRole("button", { name: "Monter Portail bailleurs" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Descendre Facturation" }),
    ).toBeDisabled();
  });

  it("supposes somebody else carries a mission", async () => {
    const onStaff = vi.fn();
    draw([aMission()], { onStaff });

    await userEvent.click(
      screen.getByRole("button", {
        name: "Changer les intervenants de Portail bailleurs",
      }),
    );
    await userEvent.click(screen.getByRole("button", { name: /Bob Durand/ }));

    expect(onStaff).toHaveBeenCalledWith(10, [2]);
  });

  it("offers the whole team on a mission nobody is on yet", async () => {
    // The blockage the screen exists to lift: « Sans intervenant » must be
    // one click away from being fixed, at least as a hypothesis.
    draw([aMission({ assignees: [], blocker: "no_assignee", ends_on: null })]);

    expect(screen.getByText("Affecter")).toBeInTheDocument();
    await userEvent.click(
      screen.getByRole("button", {
        name: "Changer les intervenants de Portail bailleurs",
      }),
    );

    expect(screen.getByRole("button", { name: /Alice Martin/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Bob Durand/ })).toBeInTheDocument();
  });

  it("says why a mission carries no date instead of leaving it blank", () => {
    draw([aMission({ blocker: "no_estimate", ends_on: null, remaining_days: 0 })]);

    expect(screen.getByText("Sans estimation")).toBeInTheDocument();
    expect(
      screen.getByTitle("Estimez le build pour la placer dans le plan"),
    ).toBeInTheDocument();
  });

  it("announces an empty backlog in its own words", () => {
    draw([]);

    expect(screen.getByText(/Aucune mission à planifier/)).toBeInTheDocument();
  });
});

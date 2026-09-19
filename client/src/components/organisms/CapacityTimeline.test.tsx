import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { CapacityTimeline } from "./CapacityTimeline";
import type { PersonLoadResponse } from "@/lib/api/generated/model";

const WEEKS = ["2026-09-14", "2026-09-21"];

function aPerson(overrides: Partial<PersonLoadResponse> = {}): PersonLoadResponse {
  return {
    user: { id: 1, display_name: "Alice Martin", initials: "AM" },
    weeks: [
      {
        week: "2026-09-14",
        capacity: 5,
        booked: 5,
        projected: 1,
        reserved: 0.5,
        free: 0,
        is_overloaded: true,
      },
      {
        week: "2026-09-21",
        capacity: 5,
        booked: 1,
        projected: 0,
        reserved: 0.5,
        free: 3.5,
        is_overloaded: false,
      },
    ],
    free_days: 3.5,
    first_free_week: "2026-09-21",
    ...overrides,
  };
}

describe("CapacityTimeline", () => {
  it("says how much room someone has left over the horizon", () => {
    render(<CapacityTimeline people={[aPerson()]} weeks={WEEKS} />);

    expect(screen.getByText("3,5")).toBeInTheDocument();
  });

  it("says from when someone frees up, not merely that they are taken", () => {
    render(<CapacityTimeline people={[aPerson()]} weeks={WEEKS} />);

    expect(screen.getByText("Semaine du 21 sept.")).toBeInTheDocument();
  });

  it("says so plainly when someone never frees up", () => {
    render(
      <CapacityTimeline
        people={[aPerson({ free_days: 0, first_free_week: null })]}
        weeks={WEEKS}
      />,
    );

    expect(screen.getByText("Aucune")).toBeInTheDocument();
  });

  it("keeps what is declared apart from what is projected", () => {
    render(<CapacityTimeline people={[aPerson()]} weeks={WEEKS} />);

    expect(
      screen.getByTitle("5 j déclarés, 1 j projetés, 0,5 j réservés sur 5 j"),
    ).toBeInTheDocument();
  });

  it("announces an empty team in its own words", () => {
    render(<CapacityTimeline people={[]} weeks={WEEKS} />);

    expect(screen.getByText(/Aucun intervenant actif/)).toBeInTheDocument();
  });
});

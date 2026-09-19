import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MoodTrendRow } from "./MoodTrendRow";
import type { DayMoodsResponse } from "@/lib/api/generated/model";

const day = (overrides: Partial<DayMoodsResponse> = {}): DayMoodsResponse =>
  ({
    day: "2026-09-18",
    moods: [],
    counts: {},
    average: null,
    participation: 0,
    ...overrides,
  }) as DayMoodsResponse;

function show(value: DayMoodsResponse, headcount = 4) {
  return render(
    <table>
      <tbody>
        <MoodTrendRow day={value} headcount={headcount} isToday={false} />
      </tbody>
    </table>,
  );
}

describe("MoodTrendRow", () => {
  it("sums the day up rather than naming anyone", () => {
    show(
      day({
        participation: 2,
        average: 4.5,
        counts: { good: 1, excellent: 1 },
        moods: [
          {
            author: { id: 1, display_name: "Léa Chen", initials: "LC" },
            level: "good",
          },
        ],
      }),
    );

    expect(screen.getByText("4,5")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    // Who said what belongs to the record: repeating it would make the two
    // tabs the same screen twice.
    expect(screen.queryByText("LC")).not.toBeInTheDocument();
  });

  it("says nothing of a day nobody answered for", () => {
    show(day());

    expect(screen.getByText("—")).toBeInTheDocument();
    expect(screen.getByLabelText("Aucune réponse")).toBeInTheDocument();
  });
});

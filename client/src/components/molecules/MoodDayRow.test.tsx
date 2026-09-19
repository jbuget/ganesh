import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MoodDayRow } from "./MoodDayRow";
import type { DayMoodsResponse } from "@/lib/api/generated/model";

const author = (id: number, name: string, initials: string) => ({
  id,
  display_name: name,
  initials,
});

const day = (overrides: Partial<DayMoodsResponse> = {}): DayMoodsResponse =>
  ({
    day: "2026-09-18",
    moods: [],
    counts: {},
    average: null,
    participation: 0,
    ...overrides,
  }) as DayMoodsResponse;

function show(value: DayMoodsResponse, headcount = 4, isToday = false) {
  render(
    <table>
      <tbody>
        <MoodDayRow day={value} headcount={headcount} isToday={isToday} />
      </tbody>
    </table>,
  );
}

describe("MoodDayRow", () => {
  it("names the day and dates it", () => {
    show(day());

    expect(screen.getByText("vendredi 18 sept.")).toBeInTheDocument();
  });

  it("marks today, so a window opening on a Friday is not misread", () => {
    show(day(), 4, true);

    expect(screen.getByText("aujourd'hui")).toBeInTheDocument();
  });

  it("reads the answers against the headcount", () => {
    show(
      day({
        participation: 2,
        moods: [
          { author: author(1, "Léa Chen", "LC"), level: "bad" },
          { author: author(2, "Gabriel Belhadj", "GB"), level: "good" },
        ],
      }),
      9,
    );

    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("/ 9")).toBeInTheDocument();
    expect(screen.getByText("LC")).toBeInTheDocument();
    expect(screen.getByText("GB")).toBeInTheDocument();
  });

  it("says a silent day is silent, rather than leaving a blank", () => {
    show(day());

    expect(screen.getByText("Personne n'a répondu")).toBeInTheDocument();
  });
});

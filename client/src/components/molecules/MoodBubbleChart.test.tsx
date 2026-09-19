import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MoodBubbleChart } from "./MoodBubbleChart";
import type { DayMoodsResponse } from "@/lib/api/generated/model";

const day = (
  iso: string,
  counts: DayMoodsResponse["counts"],
  average: number | null,
): DayMoodsResponse =>
  ({
    day: iso,
    moods: [],
    counts,
    average,
    participation: Object.values(counts).reduce((sum, n) => sum + (n ?? 0), 0),
  }) as DayMoodsResponse;

describe("MoodBubbleChart", () => {
  it("bands the levels with the best on top", () => {
    render(<MoodBubbleChart days={[day("2026-09-18", {}, null)]} />);

    const bands = screen.getAllByText(/Excellente|Bonne|Neutre|Difficile|Mauvaise/);
    expect(bands.map((band) => band.textContent)).toEqual([
      "Excellente",
      "Bonne",
      "Neutre",
      "Difficile",
      "Mauvaise",
    ]);
  });

  it("runs the days oldest first, against the record it sits beside", () => {
    // The API hands the window over most recent first; time reads left to
    // right, and a window read backwards makes every drift look like a
    // recovery.
    render(
      <MoodBubbleChart
        days={[day("2026-09-18", {}, null), day("2026-09-17", {}, null)]}
      />,
    );

    const labels = screen.getAllByText(/sept\./);
    expect(labels.map((label) => label.textContent)).toEqual(["17 sept.", "18 sept."]);
  });

  it("draws one circle per level answered, and none for the rest", () => {
    const { container } = render(
      <MoodBubbleChart days={[day("2026-09-18", { good: 3, bad: 1 }, 3.5)]} />,
    );

    expect(container.querySelectorAll("span[style]")).toHaveLength(2);
  });

  it("carries the mean over the bubbles it came from", () => {
    const { container } = render(
      <MoodBubbleChart days={[day("2026-09-18", { good: 2 }, 4)]} />,
    );

    expect(container.querySelector("polyline")).toBeInTheDocument();
  });
});

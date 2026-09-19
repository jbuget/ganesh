import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MoodsTable } from "./MoodsTable";
import type { DayMoodsResponse } from "@/lib/api/generated/model";

const day = (iso: string, moods: DayMoodsResponse["moods"] = []): DayMoodsResponse =>
  ({
    day: iso,
    moods,
    counts: {},
    average: null,
    participation: moods.length,
  }) as DayMoodsResponse;

const signed = (id: number, name: string, initials: string) => ({
  author: { id, display_name: name, initials },
  level: "good" as const,
});

describe("MoodsTable", () => {
  it("draws the window in the order it is given, most recent first", () => {
    render(
      <MoodsTable
        days={[day("2026-09-18"), day("2026-09-17")]}
        headcount={4}
        today="2026-09-18"
      />,
    );

    const rows = screen.getAllByText(/sept\./);
    expect(rows.map((row) => row.textContent)).toEqual([
      "vendredi 18 sept.",
      "jeudi 17 sept.",
    ]);
  });

  it("closes the column that names the day off from those describing it", () => {
    // The frame is shared with the teammates and the mission reference list:
    // two tables that read alike must not be able to drift apart.
    render(<MoodsTable days={[day("2026-09-18")]} headcount={4} today="2026-09-18" />);

    expect(screen.getByRole("columnheader", { name: "Jour" })).toHaveClass(
      "border-r-slate-500",
    );
  });

  it("names the columns the window is read through", () => {
    render(<MoodsTable days={[day("2026-09-18")]} headcount={4} today="2026-09-18" />);

    expect(screen.getAllByRole("columnheader").map((head) => head.textContent)).toEqual(
      ["Jour", "Réponses", "Moral"],
    );
  });

  it("marks today, and it alone", () => {
    render(
      <MoodsTable
        days={[day("2026-09-18"), day("2026-09-17")]}
        headcount={4}
        today="2026-09-18"
      />,
    );

    expect(screen.getAllByText("aujourd'hui")).toHaveLength(1);
  });

  it("hands the answers over to the rows", () => {
    render(
      <MoodsTable
        days={[day("2026-09-18", [signed(1, "Léa Chen", "LC")])]}
        headcount={4}
        today="2026-09-18"
      />,
    );

    expect(screen.getByText("LC")).toBeInTheDocument();
    expect(screen.getByText("/ 4")).toBeInTheDocument();
  });
});

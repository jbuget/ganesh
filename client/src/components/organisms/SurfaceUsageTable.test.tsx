import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SurfaceUsageTable } from "./SurfaceUsageTable";
import type {
  Surface,
  SurfaceActivityResponse,
  SurfaceUsageResponse,
} from "@/lib/api/generated/model";

const activity = (
  surface: Surface,
  people = 0,
  gestures = 0,
  delta_in_people = 0,
  last_used_on: string | null = null,
): SurfaceActivityResponse => ({
  surface,
  people,
  gestures,
  delta_in_people,
  last_used_on,
});

const usage = (
  activities: SurfaceActivityResponse[],
  idle_count = 0,
): SurfaceUsageResponse => ({ activities, idle_count });

describe("SurfaceUsageTable", () => {
  it("names each function in French, and says what is counted where it is not obvious", () => {
    render(
      <SurfaceUsageTable
        usage={usage([activity("machine_access", 1, 2, 0, "2026-09-16")])}
      />,
    );

    expect(screen.getByText("Accès machine")).toBeInTheDocument();
    expect(screen.getByText(/seul leur dernier appel est connu/)).toBeInTheDocument();
  });

  it("draws the functions in the order it is given", () => {
    // The domain's order, never a ranking: sorted by traffic, the idle lines
    // would sink to where nobody reads them.
    render(
      <SurfaceUsageTable
        usage={usage([
          activity("time_entry", 9, 42),
          activity("gazette"),
          activity("mood", 4, 12),
        ])}
      />,
    );

    const rows = screen.getAllByRole("row").slice(1);
    const named = rows.map(
      (row) => within(row).getAllByRole("cell")[0].querySelector("span")?.textContent,
    );
    expect(named).toEqual(["Saisie des temps", "La Gazette", "Moral"]);
  });

  it("reads a function's people, gestures and movement", () => {
    render(
      <SurfaceUsageTable
        usage={usage([activity("project_updates", 3, 11, -2, "2026-09-16")])}
      />,
    );

    const cells = within(screen.getAllByRole("row")[1]).getAllByRole("cell");
    expect(cells.map((cell) => cell.textContent)).toEqual([
      "Actualités de projet",
      "3",
      "11",
      "−2",
      "16 sept. 2026",
    ]);
  });

  it("marks a function nobody used, on the figure and not on the whole line", () => {
    // Colour marks, it does not fill: eight tinted rows would read as a
    // broken screen rather than as a reading.
    render(<SurfaceUsageTable usage={usage([activity("planning")], 1)} />);

    const row = screen.getAllByRole("row")[1];
    const [, people, gestures] = within(row).getAllByRole("cell");
    expect(gestures).toHaveClass("text-amber-600");
    expect(people).not.toHaveClass("text-amber-600");
    expect(row.className).not.toContain("amber");
  });

  it("says « jamais » for a function nobody has ever used", () => {
    render(<SurfaceUsageTable usage={usage([activity("gazette")], 1)} />);

    expect(screen.getByText("jamais")).toBeInTheDocument();
  });

  it("counts what served nobody, and names the screens it cannot see", () => {
    render(<SurfaceUsageTable usage={usage([activity("gazette")], 3)} />);

    expect(
      screen.getByText(/3 fonctions n'ont servi à personne sur la période\./),
    ).toBeInTheDocument();
    expect(screen.getByText(/ne font que lire/)).toBeInTheDocument();
  });

  it("says that the last use escapes the window", () => {
    render(<SurfaceUsageTable usage={usage([activity("gazette")], 1)} />);

    expect(screen.getByText("à ce jour")).toBeInTheDocument();
  });

  it("closes the column that names the function off from those describing it", () => {
    // The frame is shared with the teammates and the mission reference list:
    // two tables that read alike must not be able to drift apart.
    render(<SurfaceUsageTable usage={usage([activity("time_entry", 1, 1)])} />);

    const naming = within(screen.getAllByRole("row")[1]).getAllByRole("cell")[0];
    expect(naming.className).toContain("border-r-slate-500");
  });
});

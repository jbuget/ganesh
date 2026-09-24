import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { MonthBriefing } from "./MonthBriefing";

const SETTLED = {
  cursor: { year: 2026, month: 9 },
  actualDays: 12,
  forecastDays: 3,
  workingDays: 22,
  monthsToSettle: [],
  daysMissing: [],
  missionsToDeclare: [],
};

describe("MonthBriefing", () => {
  it("names the month it speaks of", () => {
    render(<MonthBriefing {...SETTLED} />);

    expect(screen.getByRole("heading", { name: "septembre 2026" })).toBeInTheDocument();
  });

  it("tells delivered from forecast: what is planned must not read as done", () => {
    render(<MonthBriefing {...SETTLED} />);

    expect(screen.getByText(/12 j/)).toBeInTheDocument();
    expect(screen.getByText(/3 j prévus/)).toBeInTheDocument();
    expect(screen.getByText(/22 jours ouvrés/)).toBeInTheDocument();
  });

  it("says so when nothing is waiting, rather than showing an empty list", () => {
    render(<MonthBriefing {...SETTLED} />);

    expect(screen.getByText(/Tout est à jour/)).toBeInTheDocument();
  });

  it("links the month left open to the month itself, not to the one running", () => {
    render(
      <MonthBriefing
        {...SETTLED}
        monthsToSettle={[{ year: 2026, month: 8, isEmpty: false }]}
      />,
    );

    expect(screen.getByText(/août 2026/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Valider" })).toHaveAttribute(
      "href",
      "/timesheet?month=2026-08",
    );
  });

  it("names every month left behind, the closest one first", () => {
    render(
      <MonthBriefing
        {...SETTLED}
        monthsToSettle={[
          { year: 2026, month: 8, isEmpty: false },
          { year: 2026, month: 7, isEmpty: true },
          { year: 2026, month: 6, isEmpty: true },
        ]}
      />,
    );

    const lines = screen.getAllByRole("listitem").map((line) => line.textContent);

    expect(lines[0]).toMatch(/août 2026/);
    expect(lines[1]).toMatch(/juillet 2026/);
    expect(lines[2]).toMatch(/juin 2026/);
  });

  it("asks to fill in a month never entered, not to validate it", () => {
    render(
      <MonthBriefing
        {...SETTLED}
        monthsToSettle={[{ year: 2026, month: 7, isEmpty: true }]}
      />,
    );

    expect(screen.getByText(/n'a aucun temps saisi/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Saisir" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Valider" })).not.toBeInTheDocument();
  });

  it("counts the days missing, in the singular when there is one", () => {
    const { rerender } = render(
      <MonthBriefing {...SETTLED} daysMissing={["2026-09-15"]} />,
    );

    expect(
      screen.getByText("1 jour ouvré déjà passé est sans saisie."),
    ).toBeInTheDocument();

    rerender(<MonthBriefing {...SETTLED} daysMissing={["2026-09-15", "2026-09-16"]} />);

    expect(
      screen.getByText("2 jours ouvrés déjà passés sont sans saisie."),
    ).toBeInTheDocument();
  });

  it("names the missions one contributes to with nothing declared on them", () => {
    render(
      <MonthBriefing
        {...SETTLED}
        missionsToDeclare={[
          { projectId: 1, projectLabel: "Portail bailleurs" },
          { projectId: 2, projectLabel: "Refonte extranet" },
        ]}
      />,
    );

    expect(screen.getByText("Portail bailleurs")).toBeInTheDocument();
    expect(screen.getByText("Refonte extranet")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Déclarer" })).toHaveAttribute(
      "href",
      "/timesheet",
    );
  });

  it("stops saying all is well as soon as something is waiting", () => {
    render(<MonthBriefing {...SETTLED} daysMissing={["2026-09-15"]} />);

    expect(screen.queryByText(/Tout est à jour/)).not.toBeInTheDocument();
  });
});

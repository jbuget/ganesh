import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { CoverageCurve } from "./CoverageCurve";

const WEEKS = [
  { weekStart: "2026-08-31", rate: 0.6, declaredDays: 9, expectedDays: 15 },
  { weekStart: "2026-09-07", rate: 0.8, declaredDays: 12, expectedDays: 15 },
  { weekStart: "2026-09-14", rate: 0.9, declaredDays: 13.5, expectedDays: 15 },
];

describe("CoverageCurve", () => {
  it("says in words where the curve starts and where it ends", () => {
    render(<CoverageCurve points={WEEKS} />);

    expect(
      screen.getByRole("img", {
        name: "Couverture par semaine sur 3 semaines : de 60 % à 90 %",
      }),
    ).toBeInTheDocument();
  });

  it("holds every week as a figure for whoever cannot see the line", () => {
    render(<CoverageCurve points={WEEKS} />);

    expect(screen.getByRole("row", { name: /7 sept\. 80 %/ })).toBeInTheDocument();
  });

  it("breaks the line over a week nobody was expected in", () => {
    // A holiday week is not a collapse: joining across it would draw one.
    const { container } = render(
      <CoverageCurve points={[WEEKS[0], { ...WEEKS[1], rate: null }, WEEKS[2]]} />,
    );

    expect(container.querySelectorAll("path[data-line]")).toHaveLength(2);
  });

  it("leaves a week with nothing to read out of the table's figures", () => {
    render(
      <CoverageCurve points={[WEEKS[0], { ...WEEKS[1], rate: null }, WEEKS[2]]} />,
    );

    expect(screen.getByRole("row", { name: /7 sept\. —/ })).toBeInTheDocument();
  });

  it("says plainly when no week expected anything", () => {
    render(
      <CoverageCurve
        points={[
          { weekStart: "2026-09-07", rate: null, declaredDays: 0, expectedDays: 0 },
        ]}
      />,
    );

    expect(
      screen.getByText("Aucune semaine n'attendait de saisie."),
    ).toBeInTheDocument();
  });

  it("gives nothing away until the pointer is over a week", () => {
    render(<CoverageCurve points={WEEKS} />);

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("details the week under the pointer: its rate and the days behind it", async () => {
    const { container } = render(<CoverageCurve points={WEEKS} />);

    await userEvent.hover(container.querySelector("[data-week='2026-09-07']")!);

    const tooltip = screen.getByRole("tooltip");
    expect(tooltip).toHaveTextContent("Semaine du 7 sept.");
    expect(tooltip).toHaveTextContent("80 %");
    expect(tooltip).toHaveTextContent("12 / 15 jours-personnes");
  });

  it("follows the pointer from one week to the next", async () => {
    const { container } = render(<CoverageCurve points={WEEKS} />);

    await userEvent.hover(container.querySelector("[data-week='2026-09-07']")!);
    await userEvent.hover(container.querySelector("[data-week='2026-09-14']")!);

    expect(screen.getByRole("tooltip")).toHaveTextContent("13,5 / 15 jours-personnes");
  });

  it("puts the detail away when the pointer leaves", async () => {
    const { container } = render(<CoverageCurve points={WEEKS} />);

    await userEvent.hover(container.querySelector("[data-week='2026-09-07']")!);
    await userEvent.unhover(container.querySelector("svg")!);

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("has nothing to detail for a week nobody was expected in", () => {
    const { container } = render(
      <CoverageCurve
        points={[WEEKS[0], { ...WEEKS[1], rate: null, expectedDays: 0 }, WEEKS[2]]}
      />,
    );

    expect(container.querySelector("[data-week='2026-09-07']")).toBeNull();
  });
});

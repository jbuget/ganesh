import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { ActivityMosaic } from "./ActivityMosaic";

// Thursday 8 to Tuesday 13 October 2026.
const DAYS = [
  { day: "2026-10-08", gestures: 0 },
  { day: "2026-10-09", gestures: 4 },
  { day: "2026-10-10", gestures: 0 },
  { day: "2026-10-11", gestures: 0 },
  { day: "2026-10-12", gestures: 1 },
  { day: "2026-10-13", gestures: 2 },
];

describe("ActivityMosaic", () => {
  it("draws one cell per day of the window", () => {
    render(<ActivityMosaic days={DAYS} />);

    expect(screen.getAllByRole("img")).toHaveLength(6);
  });

  it("says in words what a day holds, in French and in the singular when it is one", () => {
    render(<ActivityMosaic days={DAYS} />);

    expect(screen.getByLabelText("4 gestes le vendredi 9 octobre")).toBeInTheDocument();
    expect(screen.getByLabelText("1 geste le lundi 12 octobre")).toBeInTheDocument();
    expect(
      screen.getByLabelText("Aucun geste le samedi 10 octobre"),
    ).toBeInTheDocument();
  });

  it("totals the gestures of the window", () => {
    render(<ActivityMosaic days={DAYS} />);

    expect(screen.getByText("7 gestes sur l'année écoulée")).toBeInTheDocument();
  });

  it("says so in words when nothing happened", () => {
    render(<ActivityMosaic days={DAYS.map((entry) => ({ ...entry, gestures: 0 }))} />);

    expect(screen.getByText("Aucun geste sur la période.")).toBeInTheDocument();
  });

  it("opens the detail of a day as soon as the pointer reaches it", () => {
    render(<ActivityMosaic days={DAYS} />);

    fireEvent.mouseEnter(screen.getByLabelText("1 geste le lundi 12 octobre"));

    const tooltip = screen.getByRole("tooltip");
    expect(tooltip).toHaveTextContent("lundi 12 octobre");
    expect(tooltip).toHaveTextContent("14,3 % de l'année");
  });

  it("says when a day is the busiest of the year", () => {
    render(<ActivityMosaic days={DAYS} />);

    fireEvent.mouseEnter(screen.getByLabelText("4 gestes le vendredi 9 octobre"));

    expect(screen.getByRole("tooltip")).toHaveTextContent(
      "Le jour le plus chargé de l'année",
    );
  });

  it("closes it when the pointer leaves", () => {
    render(<ActivityMosaic days={DAYS} />);
    const cell = screen.getByLabelText("1 geste le lundi 12 octobre");

    fireEvent.mouseEnter(cell);
    fireEvent.mouseLeave(cell);

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });
});

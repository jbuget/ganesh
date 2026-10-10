import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { ActivityDayDetail } from "./ActivityDayDetail";

describe("ActivityDayDetail", () => {
  it("says which day it is, and how much it holds", () => {
    render(<ActivityDayDetail day="2026-10-09" gestures={4} busiest={10} total={40} />);

    expect(screen.getByText("vendredi 9 octobre")).toBeInTheDocument();
    expect(screen.getByText("4 gestes")).toBeInTheDocument();
    expect(screen.getByText("10 % de l'année")).toBeInTheDocument();
  });

  it("says when it is the busiest day of the year", () => {
    render(
      <ActivityDayDetail day="2026-10-09" gestures={10} busiest={10} total={40} />,
    );

    expect(screen.getByText("Le jour le plus chargé de l'année")).toBeInTheDocument();
  });

  it("says so plainly when nothing happened", () => {
    render(<ActivityDayDetail day="2026-10-10" gestures={0} busiest={10} total={40} />);

    expect(screen.getByText("Aucun geste")).toBeInTheDocument();
  });
});

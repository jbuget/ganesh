import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { RoadmapSummaryBar } from "./RoadmapSummaryBar";

describe("RoadmapSummaryBar", () => {
  it("says what the drawing holds, and what is missing from it", () => {
    render(
      <RoadmapSummaryBar
        summary={{
          missions: 14,
          late: 3,
          undated: 5,
          unestimated: 2,
          delivered: 4,
        }}
      />,
    );

    expect(screen.getByText("14")).toBeInTheDocument();
    expect(screen.getByText("projets")).toBeInTheDocument();
    expect(screen.getByText("en retard")).toBeInTheDocument();
    expect(screen.getByText("sans date")).toBeInTheDocument();
    expect(screen.getByText("sans estimation")).toBeInTheDocument();
  });

  it("speaks of one project in the singular", () => {
    render(
      <RoadmapSummaryBar
        summary={{ missions: 1, late: 0, undated: 0, unestimated: 0, delivered: 1 }}
      />,
    );

    expect(screen.getByText("projet")).toBeInTheDocument();
    expect(screen.getByText("mise en service")).toBeInTheDocument();
  });
});

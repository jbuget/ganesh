import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { CoverageHeadline } from "./CoverageHeadline";

const COVERAGE = {
  declared_days: 142,
  expected_days: 163,
  missing_days: 21,
  rate: 142 / 163,
  delta_in_points: 6,
};

describe("CoverageHeadline", () => {
  it("shows the coverage rate as the lead figure", () => {
    render(<CoverageHeadline coverage={COVERAGE} medianDelay={1.5} />);

    expect(screen.getByText("87 %")).toBeInTheDocument();
  });

  it("says what the rate is measured against", () => {
    render(<CoverageHeadline coverage={COVERAGE} medianDelay={1.5} />);

    expect(screen.getByText(/142 \/ 163 jours-personnes/)).toBeInTheDocument();
  });

  it("carries the freshness alongside, never apart", () => {
    // A coverage read without its delay says nothing: 95 % filled in at D+25
    // is an administrative fiction.
    render(<CoverageHeadline coverage={COVERAGE} medianDelay={1.5} />);

    expect(screen.getByText(/délai médian de saisie : 1,5 j/)).toBeInTheDocument();
  });

  it("announces how the rate moved", () => {
    render(<CoverageHeadline coverage={COVERAGE} medianDelay={1.5} />);

    expect(screen.getByText("+6 pts")).toBeInTheDocument();
  });

  it("says plainly when a window expects nothing of anyone", () => {
    // A weekend: no rate, and no bar either.
    render(
      <CoverageHeadline
        coverage={{
          declared_days: 0,
          expected_days: 0,
          missing_days: 0,
          rate: null,
          delta_in_points: null,
        }}
        medianDelay={null}
      />,
    );

    expect(screen.getByText("—")).toBeInTheDocument();
    expect(screen.queryByRole("meter")).not.toBeInTheDocument();
  });

  it("tells what is left to declare", () => {
    render(<CoverageHeadline coverage={COVERAGE} medianDelay={1.5} />);

    expect(screen.getByText(/21 jours-personnes à déclarer/)).toBeInTheDocument();
  });

  it("says nothing is left when the period is fully declared", () => {
    render(
      <CoverageHeadline
        coverage={{
          declared_days: 80,
          expected_days: 80,
          missing_days: 0,
          rate: 1,
          delta_in_points: 0,
        }}
        medianDelay={1}
      />,
    );

    expect(screen.queryByText(/à déclarer/)).not.toBeInTheDocument();
  });
});

import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { TrendBadge } from "./TrendBadge";

describe("TrendBadge", () => {
  it("announces a rise against the previous window", () => {
    render(<TrendBadge points={6} />);

    expect(screen.getByText("+6 pts")).toBeInTheDocument();
  });

  it("announces a fall", () => {
    render(<TrendBadge points={-4} />);

    expect(screen.getByText("−4 pts")).toBeInTheDocument();
  });

  it("says against what the movement is read", () => {
    render(<TrendBadge points={6} />);

    expect(screen.getByRole("status")).toHaveTextContent(
      "+6 pts par rapport à la période précédente",
    );
  });

  it("carries no fixed identifier, so it may be drawn twice", () => {
    // An atom is reusable by nature: two badges sharing one id would make the
    // document invalid and the description ambiguous.
    const { container } = render(
      <>
        <TrendBadge points={6} />
        <TrendBadge points={-2} />
      </>,
    );

    expect(container.querySelectorAll("[id]")).toHaveLength(0);
  });

  it("shows nothing without a comparable window", () => {
    // Nothing was expected of the previous window: there is no movement to
    // announce, and a « +0 pt » would invent one.
    const { container } = render(<TrendBadge points={null} />);

    expect(container).toBeEmptyDOMElement();
  });

  it("names a flat window rather than signing it", () => {
    render(<TrendBadge points={0} />);

    expect(screen.getByText("stable")).toBeInTheDocument();
  });
});

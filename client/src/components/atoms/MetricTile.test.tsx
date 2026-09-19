import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { MetricTile } from "./MetricTile";

describe("MetricTile", () => {
  it("names the figure it shows", () => {
    render(<MetricTile label="Délai médian de saisie" value="1,5 j" />);

    expect(screen.getByText("Délai médian de saisie")).toBeInTheDocument();
    expect(screen.getByText("1,5 j")).toBeInTheDocument();
  });

  it("carries the reading that makes the figure understandable", () => {
    render(
      <MetricTile label="Mois validés" value="75 %" hint="9 mois sur 12 verrouillés" />,
    );

    expect(screen.getByText("9 mois sur 12 verrouillés")).toBeInTheDocument();
  });

  it("stands out when the figure calls for attention", () => {
    // A late catch-up is not an error: it is a figure to go and look at.
    const { container } = render(
      <MetricTile label="Rattrapés tard" value="32 %" tone="warning" />,
    );

    expect(container.firstChild).toHaveAttribute("data-tone", "warning");
  });

  it("is plain by default", () => {
    const { container } = render(<MetricTile label="Projets actifs" value="30" />);

    expect(container.firstChild).toHaveAttribute("data-tone", "plain");
  });
});

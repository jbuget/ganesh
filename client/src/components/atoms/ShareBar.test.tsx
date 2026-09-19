import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { ShareBar } from "./ShareBar";

describe("ShareBar", () => {
  it("names what the bar measures, and how much", () => {
    render(<ShareBar label="Réalisation" days={12} share={0.4} />);

    expect(screen.getByText("Réalisation")).toBeInTheDocument();
    expect(screen.getByText("12 j")).toBeInTheDocument();
    expect(screen.getByText("40 %")).toBeInTheDocument();
  });

  it("draws the bar to the width of its share", () => {
    render(<ShareBar label="Réalisation" days={12} share={0.4} />);

    expect(screen.getByRole("meter")).toHaveStyle({ width: "40%" });
  });

  it("stays readable by a screen reader without the bar", () => {
    render(<ShareBar label="Réalisation" days={12} share={0.4} />);

    const meter = screen.getByRole("meter");
    expect(meter).toHaveAttribute("aria-valuenow", "40");
    expect(meter).toHaveAttribute("aria-label", "Réalisation");
  });

  it("draws nothing when the share is unknown", () => {
    render(<ShareBar label="Réalisation" days={0} share={null} />);

    expect(screen.getByText("—")).toBeInTheDocument();
    expect(screen.queryByRole("meter")).not.toBeInTheDocument();
  });

  it("carries the colour that places what it measures", () => {
    // Phases and axes are recognised by their colour elsewhere in the app: a
    // bar of a different shade would break the reading.
    render(<ShareBar label="Réalisation" days={12} share={0.4} colour="bg-blue-500" />);

    expect(screen.getByRole("meter")).toHaveClass("bg-blue-500");
  });
});

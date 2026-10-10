import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { CountBar } from "./CountBar";

describe("CountBar", () => {
  it("states the count beside its name", () => {
    render(<CountBar label="Déposés" count={6} max={6} />);

    expect(screen.getByText("Déposés")).toBeInTheDocument();
    expect(screen.getByText("6")).toBeInTheDocument();
  });

  it("sizes the bar against the largest line", () => {
    render(<CountBar label="Refusés" count={3} max={6} />);

    expect(screen.getByRole("meter", { name: "Refusés" })).toHaveStyle({
      width: "50%",
    });
  });

  it("draws an empty bar rather than dividing by zero", () => {
    render(<CountBar label="Refusés" count={0} max={0} />);

    expect(screen.getByRole("meter", { name: "Refusés" })).toHaveStyle({ width: "0%" });
  });
});

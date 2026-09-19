import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { PersonLoadCell } from "./PersonLoadCell";

describe("PersonLoadCell", () => {
  it("counts what is declared together with what is projected", () => {
    render(
      <PersonLoadCell capacity={5} booked={2} projected={1} isOverloaded={false} />,
    );

    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("tells the two apart in what it announces", () => {
    // A fact and a hypothesis must never read as the same thing.
    const { container } = render(
      <PersonLoadCell capacity={5} booked={2} projected={1} isOverloaded={false} />,
    );

    expect(container.querySelector("[title]")?.getAttribute("title")).toBe(
      "2 j déclarés, 1 j projetés sur 5 j",
    );
  });

  it("marks an over-booked week out", () => {
    const { container } = render(
      <PersonLoadCell capacity={5} booked={5} projected={2} isOverloaded={true} />,
    );

    expect(container.innerHTML).toContain("text-red-600");
  });

  it("strikes a week with no working day rather than showing it empty", () => {
    render(
      <PersonLoadCell capacity={0} booked={0} projected={0} isOverloaded={false} />,
    );

    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("leaves an untouched week blank", () => {
    render(
      <PersonLoadCell capacity={5} booked={0} projected={0} isOverloaded={false} />,
    );

    expect(screen.queryByText("0")).not.toBeInTheDocument();
  });
});

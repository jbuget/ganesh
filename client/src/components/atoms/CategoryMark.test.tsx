import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { CategoryMark } from "./CategoryMark";

describe("CategoryMark", () => {
  it("writes the axis in ordinary text", () => {
    render(<CategoryMark value="innovate_differentiate" />);

    expect(screen.getByText("Innover & différencier")).toBeInTheDocument();
  });

  it("marks the axis with a square bullet, distinct from a phase's dot", () => {
    const { container } = render(<CategoryMark value="innovate_differentiate" />);

    const bullet = container.querySelector("span span");
    expect(bullet?.getAttribute("class")).toContain("rounded-[3px]");
  });

  it("marks nothing without an axis", () => {
    const { container } = render(<CategoryMark value={null} />);

    expect(container).toBeEmptyDOMElement();
  });
});

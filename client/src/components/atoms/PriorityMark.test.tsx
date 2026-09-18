import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { PriorityMark } from "./PriorityMark";

describe("PriorityMark", () => {
  it("spells the level out in full", () => {
    render(<PriorityMark value="high" />);

    expect(screen.getByText("Haute")).toBeInTheDocument();
  });

  it("gives each level a distinct drawing, and not just a shade", () => {
    // Without colour — colour blindness, print, a poorly calibrated screen — it
    // is how full the gauge is that must carry the scale.
    const formes = (["critical", "high", "normal", "low"] as const).map((niveau) => {
      const { container, unmount } = render(<PriorityMark value={niveau} />);
      const className = container.querySelector("svg")?.getAttribute("class") ?? "";
      const forme = className.split(" ").find((c) => c.startsWith("lucide-"));
      unmount();
      return forme;
    });

    expect(new Set(formes).size).toBe(4);
  });

  it("marks nothing without a priority", () => {
    const { container } = render(<PriorityMark value={null} />);

    expect(container).toBeEmptyDOMElement();
  });
});

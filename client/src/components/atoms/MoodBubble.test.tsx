import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MoodBubble } from "./MoodBubble";

const sizeOf = (container: HTMLElement) =>
  Number.parseFloat((container.querySelector("span") as HTMLElement).style.width);

describe("MoodBubble", () => {
  it("draws nothing where nobody answered", () => {
    const { container } = render(<MoodBubble level="good" count={0} busiest={4} />);

    expect(container).toBeEmptyDOMElement();
  });

  it("gives the busiest cell the largest circle", () => {
    const { container } = render(<MoodBubble level="good" count={4} busiest={4} />);

    expect(sizeOf(container)).toBe(44);
  });

  it("scales the radius on the square root: four answers are not sixteen", () => {
    // The eye reads the area. At a quarter of the busiest cell, the circle is
    // half as wide — so it covers a quarter of the surface, as it should.
    const quarter = render(<MoodBubble level="good" count={1} busiest={4} />);
    const full = render(<MoodBubble level="good" count={4} busiest={4} />);

    const smallest = 10;
    expect(sizeOf(quarter.container)).toBe(smallest + (44 - smallest) * 0.5);
    expect(sizeOf(full.container)).toBe(44);
  });

  it("draws a full circle when every cell holds a single answer", () => {
    const { container } = render(<MoodBubble level="bad" count={1} busiest={1} />);

    expect(sizeOf(container)).toBe(44);
  });
});

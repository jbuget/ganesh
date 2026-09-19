import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MoodAverageLine } from "./MoodAverageLine";

const runs = (container: HTMLElement) =>
  [...container.querySelectorAll("polyline")].map((line) =>
    line.getAttribute("points"),
  );

describe("MoodAverageLine", () => {
  it("rides higher for a better mean: the best band is on top", () => {
    const { container } = render(<MoodAverageLine averages={[5, 1]} bands={5} />);

    const [best, worst] = runs(container)[0]!.split(" ");
    expect(best).toBe("25,10");
    expect(worst).toBe("75,90");
  });

  it("breaks the line on a day nobody answered, rather than dropping it", () => {
    // A silence pulled to the floor would read as a day that went badly.
    const { container } = render(<MoodAverageLine averages={[4, null, 4]} bands={5} />);

    expect(runs(container)).toHaveLength(2);
  });

  it("marks a day answered between two silences, which no segment would show", () => {
    const { container } = render(
      <MoodAverageLine averages={[null, 3, null]} bands={5} />,
    );

    const [dot] = runs(container);
    expect(dot).toBe("50,50 50,50");
  });

  it("draws nothing at all over a window nobody answered", () => {
    const { container } = render(<MoodAverageLine averages={[null, null]} bands={5} />);

    expect(container).toBeEmptyDOMElement();
  });
});

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MoodDistributionBar } from "./MoodDistributionBar";

describe("MoodDistributionBar", () => {
  it("cuts the bar in proportion to the answers", () => {
    const { container } = render(
      <MoodDistributionBar counts={{ bad: 1, good: 3 }} participation={4} />,
    );

    const segments = [...container.querySelectorAll("span")];
    expect(segments.map((segment) => segment.getAttribute("style"))).toEqual([
      "width: 25%;",
      "width: 75%;",
    ]);
  });

  it("lays the segments out in the order of the scale, worst first", () => {
    const { container } = render(
      <MoodDistributionBar counts={{ excellent: 1, bad: 1 }} participation={2} />,
    );

    const titles = [...container.querySelectorAll("span")].map((segment) =>
      segment.getAttribute("title"),
    );
    expect(titles).toEqual(["Mauvaise : 1", "Excellente : 1"]);
  });

  it("leaves a level at zero out rather than drawing a sliver of it", () => {
    const { container } = render(
      <MoodDistributionBar counts={{ good: 2, hard: 0 }} participation={2} />,
    );

    expect(container.querySelectorAll("span")).toHaveLength(1);
  });

  it("draws an empty track when nobody answered", () => {
    render(<MoodDistributionBar counts={{}} participation={0} />);

    expect(screen.getByLabelText("Aucune réponse")).toBeInTheDocument();
  });
});

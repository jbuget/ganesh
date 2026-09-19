import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MoodAverageMark } from "./MoodAverageMark";

describe("MoodAverageMark", () => {
  it("writes the mean with a comma, as figures are written here", () => {
    render(<MoodAverageMark average={3.4} />);

    expect(screen.getByText("3,4")).toBeInTheDocument();
  });

  it("places the dot along the scale, an end at each end", () => {
    const { container } = render(<MoodAverageMark average={1} />);
    expect(container.querySelector("span[style]")).toHaveStyle({ left: "0%" });

    const best = render(<MoodAverageMark average={5} />);
    expect(best.container.querySelector("span[style]")).toHaveStyle({ left: "100%" });
  });

  it("leaves the track empty when nobody answered: silence is not a bad day", () => {
    const { container } = render(<MoodAverageMark average={null} />);

    expect(screen.getByText("—")).toBeInTheDocument();
    expect(container.querySelector("span[style]")).toBeNull();
  });
});

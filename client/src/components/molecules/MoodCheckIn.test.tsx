import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { MoodCheckIn } from "./MoodCheckIn";
import { STRONG_RULE } from "@/lib/table-frame";

const TODAY = "2026-09-15";
const BEFORE = "2026-09-14";

function show(
  days: { day: string; level: "good" | "hard" | null }[],
  onPick = vi.fn(),
) {
  render(<MoodCheckIn days={days} today={TODAY} onPick={onPick} />);
  return onPick;
}

describe("MoodCheckIn", () => {
  it("names today as today, and the other day by its weekday", () => {
    show([
      { day: TODAY, level: null },
      { day: BEFORE, level: null },
    ]);

    expect(screen.getByText("Aujourd'hui")).toBeInTheDocument();
    expect(screen.getByText("lundi 14 sept.")).toBeInTheDocument();
  });

  it("says of an unanswered day that it is unanswered", () => {
    show([{ day: TODAY, level: null }]);

    expect(screen.getByText("Pas encore de réponse")).toBeInTheDocument();
  });

  it("spells out the level already answered", () => {
    show([{ day: TODAY, level: "hard" }]);

    expect(screen.getByText("Difficile")).toBeInTheDocument();
  });

  it("hands over the day along with the level", () => {
    const pick = show([
      { day: TODAY, level: null },
      { day: BEFORE, level: null },
    ]);

    fireEvent.click(screen.getAllByRole("radio", { name: "Bonne" })[1]);

    expect(pick).toHaveBeenCalledWith(BEFORE, "good");
  });

  it("shows nothing at all when no day is open", () => {
    const { container } = render(
      <MoodCheckIn days={[]} today={TODAY} onPick={vi.fn()} />,
    );

    expect(container).toBeEmptyDOMElement();
  });
});

describe("what makes it stand out", () => {
  it("closes at the weight the application closes an object at", () => {
    // Drawn like the notices around it, the one block that asks something of
    // the reader gets read like a notice.
    show([{ day: TODAY, level: null }]);

    const block = document.querySelector("section");
    expect(block?.className).toContain(STRONG_RULE);
  });
});

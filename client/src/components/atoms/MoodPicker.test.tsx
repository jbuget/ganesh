import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { MoodPicker } from "./MoodPicker";

describe("MoodPicker", () => {
  it("offers the five levels, from the worst to the best", () => {
    render(<MoodPicker value={null} onPick={vi.fn()} />);

    expect(
      screen.getAllByRole("radio").map((face) => face.getAttribute("aria-label")),
    ).toEqual(["Difficile", "Mitigée", "Bonne", "Très bonne", "Exceptionnelle"]);
  });

  it("marks nothing until one answers: the screen does not answer in one's place", () => {
    render(<MoodPicker value={null} onPick={vi.fn()} />);

    expect(
      screen
        .getAllByRole("radio")
        .every((face) => face.getAttribute("aria-checked") === "false"),
    ).toBe(true);
  });

  it("marks the level already answered, and it alone", () => {
    render(<MoodPicker value="mixed" onPick={vi.fn()} />);

    expect(screen.getByRole("radio", { name: /^Mitigée/ })).toBeChecked();
    expect(screen.getByRole("radio", { name: "Très bonne" })).not.toBeChecked();
  });

  it("hands over the level that was picked", () => {
    const pick = vi.fn();
    render(<MoodPicker value={null} onPick={pick} />);

    fireEvent.click(screen.getByRole("radio", { name: "Exceptionnelle" }));

    expect(pick).toHaveBeenCalledWith("exceptional");
  });

  it("says of the face already chosen that clicking it takes the answer back", () => {
    render(<MoodPicker value="mixed" onPick={vi.fn()} />);

    expect(screen.getByRole("radio", { name: "Mitigée — retirer" })).toHaveAttribute(
      "title",
      "Retirer",
    );
  });

  it("still offers the other levels once one has answered", () => {
    const pick = vi.fn();
    render(<MoodPicker value="great" onPick={pick} />);

    fireEvent.click(screen.getByRole("radio", { name: "Difficile" }));

    expect(pick).toHaveBeenCalledWith("hard");
  });

  it("refuses a second click while the answer travels", () => {
    const pick = vi.fn();
    render(<MoodPicker value={null} onPick={pick} disabled />);

    fireEvent.click(screen.getByRole("radio", { name: "Très bonne" }));

    expect(pick).not.toHaveBeenCalled();
  });
});

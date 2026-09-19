import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MoodLegend } from "./MoodLegend";

describe("MoodLegend", () => {
  it("names the five shades, climbing as the bars do", () => {
    render(<MoodLegend />);

    expect(screen.getAllByRole("listitem").map((entry) => entry.textContent)).toEqual([
      "Mauvaise",
      "Difficile",
      "Neutre",
      "Bonne",
      "Excellente",
    ]);
  });
});

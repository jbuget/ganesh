import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { ShareBreakdown } from "./ShareBreakdown";

const ROWS = [
  { key: "development", label: "Réalisation", days: 12, share: 0.6 },
  { key: "scoping", label: "Cadrage", days: 8, share: 0.4 },
];

describe("ShareBreakdown", () => {
  it("names what is being broken down", () => {
    render(<ShareBreakdown title="Temps par phase" rows={ROWS} />);

    expect(
      screen.getByRole("heading", { name: "Temps par phase" }),
    ).toBeInTheDocument();
  });

  it("lists every line it is given", () => {
    render(<ShareBreakdown title="Temps par phase" rows={ROWS} />);

    expect(screen.getAllByRole("meter")).toHaveLength(2);
  });

  it("says plainly when nothing was declared", () => {
    // An empty block with a title reads as a loading failure; a sentence does
    // not.
    render(<ShareBreakdown title="Temps par phase" rows={[]} />);

    expect(screen.getByText("Aucune saisie sur la période.")).toBeInTheDocument();
  });
});

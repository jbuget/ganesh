import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { PriorityMark } from "./PriorityMark";

describe("PriorityMark", () => {
  it("écrit le niveau en toutes lettres", () => {
    render(<PriorityMark value="high" />);

    expect(screen.getByText("Haute")).toBeInTheDocument();
  });

  it("donne à chaque niveau un dessin distinct, et pas qu'une teinte", () => {
    // Sans la couleur — daltonisme, impression, ecran mal calibre — c'est le
    // remplissage de la jauge qui doit porter l'echelle.
    const formes = (["critical", "high", "normal", "low"] as const).map((niveau) => {
      const { container, unmount } = render(<PriorityMark value={niveau} />);
      const className = container.querySelector("svg")?.getAttribute("class") ?? "";
      const forme = className.split(" ").find((c) => c.startsWith("lucide-"));
      unmount();
      return forme;
    });

    expect(new Set(formes).size).toBe(4);
  });

  it("ne marque rien sans priorité", () => {
    const { container } = render(<PriorityMark value={null} />);

    expect(container).toBeEmptyDOMElement();
  });
});

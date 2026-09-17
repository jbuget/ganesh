import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { PriorityMark } from "./PriorityMark";

describe("PriorityMark", () => {
  it("écrit le niveau en toutes lettres", () => {
    render(<PriorityMark valeur="haute" />);

    expect(screen.getByText("Haute")).toBeInTheDocument();
  });

  it("donne à chaque niveau une forme distincte, et pas qu'une teinte", () => {
    // Sans la couleur — daltonisme, impression, ecran mal calibre — c'est la
    // forme qui doit porter l'echelle.
    const formes = (["critique", "haute", "normale", "basse"] as const).map(
      (niveau) => {
        const { container, unmount } = render(<PriorityMark valeur={niveau} />);
        const classe = container.querySelector("svg")?.getAttribute("class") ?? "";
        const forme = classe.split(" ").find((c) => c.startsWith("lucide-"));
        unmount();
        return forme;
      },
    );

    expect(new Set(formes).size).toBe(4);
  });

  it("garde son libellé pour les lecteurs d'écran quand il est masqué", () => {
    render(<PriorityMark valeur="critique" libelleVisible={false} />);

    expect(screen.getByLabelText("Priorité critique")).toBeInTheDocument();
    expect(screen.queryByText("Critique")).toBeNull();
  });

  it("ne marque rien sans priorité", () => {
    const { container } = render(<PriorityMark valeur={null} />);

    expect(container).toBeEmptyDOMElement();
  });
});

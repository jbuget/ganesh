import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { CategoryMark } from "./CategoryMark";

describe("CategoryMark", () => {
  it("écrit l'axe en texte ordinaire", () => {
    render(<CategoryMark valeur="innover_differencier" />);

    expect(screen.getByText("Innover & différencier")).toBeInTheDocument();
  });

  it("marque l'axe d'une puce carrée, distincte de la pastille d'une phase", () => {
    const { container } = render(<CategoryMark valeur="innover_differencier" />);

    const puce = container.querySelector("span span");
    expect(puce?.getAttribute("class")).toContain("rounded-[3px]");
  });

  it("ne marque rien sans axe", () => {
    const { container } = render(<CategoryMark valeur={null} />);

    expect(container).toBeEmptyDOMElement();
  });
});

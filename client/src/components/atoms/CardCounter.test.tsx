import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MessageCircle } from "lucide-react";

import { CardCounter } from "./CardCounter";

const compteur = (nombre: number) => (
  <CardCounter
    icone={MessageCircle}
    nombre={nombre}
    libelle={["commentaire", "commentaires"]}
    vide="Aucun commentaire"
  />
);

describe("CardCounter", () => {
  it("annonce le nombre au pluriel", () => {
    render(compteur(3));

    expect(screen.getByLabelText("3 commentaires")).toHaveTextContent("3");
  });

  it("accorde au singulier", () => {
    render(compteur(1));

    expect(screen.getByLabelText("1 commentaire")).toBeInTheDocument();
  });

  it("garde l'icône sans nombre quand il n'y a rien à compter", () => {
    render(compteur(0));

    expect(screen.getByLabelText("Aucun commentaire")).toHaveTextContent("");
  });

  it("atténue l'icône quand le décompte est nul", () => {
    render(compteur(0));

    expect(screen.getByLabelText("Aucun commentaire").className).toContain(
      "text-slate-300",
    );
  });
});

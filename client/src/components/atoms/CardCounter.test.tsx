import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MessageCircle } from "lucide-react";

import { CardCounter } from "./CardCounter";

const APERCU = <p>Le cadrage commence lundi</p>;

const compteur = (nombre: number, apercu?: React.ReactNode) => (
  <CardCounter
    icone={MessageCircle}
    nombre={nombre}
    libelle={["commentaire", "commentaires"]}
    vide="Aucun commentaire"
    apercu={apercu}
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

  it("montre l'aperçu au survol", () => {
    render(compteur(2, APERCU));

    fireEvent.mouseMove(screen.getByLabelText("2 commentaires"));

    expect(screen.getByRole("tooltip")).toHaveTextContent("Le cadrage commence lundi");
  });

  it("referme l'aperçu quand la souris quitte le décompte", () => {
    render(compteur(2, APERCU));
    const decompte = screen.getByLabelText("2 commentaires");

    fireEvent.mouseMove(decompte);
    fireEvent.mouseLeave(decompte);

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("compte sans infobulle quand il n'y a rien à montrer", () => {
    render(compteur(2));

    fireEvent.mouseMove(screen.getByLabelText("2 commentaires"));

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });
});

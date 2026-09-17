import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MessageCircle } from "lucide-react";

import { CardCounter } from "./CardCounter";

const APERCU = <p>Le cadrage commence lundi</p>;

const counter = (count: number, apercu?: React.ReactNode) => (
  <CardCounter
    icon={MessageCircle}
    count={count}
    label={["commentaire", "commentaires"]}
    empty="Aucun commentaire"
    apercu={apercu}
  />
);

describe("CardCounter", () => {
  it("annonce le nombre au pluriel", () => {
    render(counter(3));

    expect(screen.getByLabelText("3 commentaires")).toHaveTextContent("3");
  });

  it("accorde au singulier", () => {
    render(counter(1));

    expect(screen.getByLabelText("1 commentaire")).toBeInTheDocument();
  });

  it("garde l'icône sans nombre quand il n'y a rien à compter", () => {
    render(counter(0));

    expect(screen.getByLabelText("Aucun commentaire")).toHaveTextContent("");
  });

  it("atténue l'icône quand le décompte est nul", () => {
    render(counter(0));

    expect(screen.getByLabelText("Aucun commentaire").className).toContain(
      "text-slate-300",
    );
  });

  it("montre l'aperçu au survol", () => {
    render(counter(2, APERCU));

    fireEvent.mouseMove(screen.getByLabelText("2 commentaires"));

    expect(screen.getByRole("tooltip")).toHaveTextContent("Le cadrage commence lundi");
  });

  it("referme l'aperçu quand la souris quitte le décompte", () => {
    render(counter(2, APERCU));
    const decompte = screen.getByLabelText("2 commentaires");

    fireEvent.mouseMove(decompte);
    fireEvent.mouseLeave(decompte);

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("compte sans infobulle quand il n'y a rien à montrer", () => {
    render(counter(2));

    fireEvent.mouseMove(screen.getByLabelText("2 commentaires"));

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });
});

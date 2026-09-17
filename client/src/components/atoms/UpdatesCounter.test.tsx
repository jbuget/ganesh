import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { UpdatesCounter } from "./UpdatesCounter";

const APERCU = <p>Le cadrage commence lundi</p>;

describe("UpdatesCounter", () => {
  it("n'affiche rien tant que le fil est vide", () => {
    const { container } = render(<UpdatesCounter nombre={0} apercu={APERCU} />);

    expect(container).toBeEmptyDOMElement();
  });

  it("compte les mises à jour du fil", () => {
    render(<UpdatesCounter nombre={3} apercu={APERCU} />);

    expect(screen.getByLabelText("3 mises à jour")).toHaveTextContent("3");
  });

  it("accorde le décompte au singulier", () => {
    render(<UpdatesCounter nombre={1} apercu={APERCU} />);

    expect(screen.getByLabelText("1 mise à jour")).toBeInTheDocument();
  });

  it("montre l'aperçu au survol", () => {
    render(<UpdatesCounter nombre={1} apercu={APERCU} />);

    fireEvent.mouseMove(screen.getByLabelText("1 mise à jour"));

    expect(screen.getByRole("tooltip")).toHaveTextContent("Le cadrage commence lundi");
  });

  it("referme l'infobulle quand la souris quitte le décompte", () => {
    render(<UpdatesCounter nombre={1} apercu={APERCU} />);
    const compteur = screen.getByLabelText("1 mise à jour");

    fireEvent.mouseMove(compteur);
    fireEvent.mouseLeave(compteur);

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("compte sans infobulle quand il n'y a rien à montrer", () => {
    render(<UpdatesCounter nombre={2} />);

    fireEvent.mouseMove(screen.getByLabelText("2 mises à jour"));

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });
});

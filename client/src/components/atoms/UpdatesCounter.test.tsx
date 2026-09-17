import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { UpdatesCounter } from "./UpdatesCounter";
import type { LastUpdateResponse } from "@/lib/api/generated/model";

const MAINTENANT = new Date("2026-09-17T12:00:00Z");

const derniere = (champs: Partial<LastUpdateResponse> = {}): LastUpdateResponse => ({
  author: { id: 1, display_name: "Léa Chen", initiales: "LÉ" },
  texte: "La **recette** commence lundi",
  publiee_le: "2026-09-17T09:00:00Z",
  ...champs,
});

describe("UpdatesCounter", () => {
  it("n'affiche rien tant que le fil est vide", () => {
    const { container } = render(
      <UpdatesCounter nombre={0} derniere={null} maintenant={MAINTENANT} />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it("compte les mises à jour du fil", () => {
    render(<UpdatesCounter nombre={3} derniere={derniere()} maintenant={MAINTENANT} />);

    expect(screen.getByLabelText("3 mises à jour")).toHaveTextContent("3");
  });

  it("accorde le décompte au singulier", () => {
    render(<UpdatesCounter nombre={1} derniere={derniere()} maintenant={MAINTENANT} />);

    expect(screen.getByLabelText("1 mise à jour")).toBeInTheDocument();
  });

  it("montre au survol qui a publié le dernier message, et quand", () => {
    render(<UpdatesCounter nombre={1} derniere={derniere()} maintenant={MAINTENANT} />);

    fireEvent.mouseMove(screen.getByLabelText("1 mise à jour"));

    expect(screen.getByRole("tooltip")).toHaveTextContent("Léa Chen");
    expect(screen.getByRole("tooltip")).toHaveTextContent("il y a 3 h");
  });

  it("donne le texte du dernier message, sans sa syntaxe", () => {
    render(<UpdatesCounter nombre={1} derniere={derniere()} maintenant={MAINTENANT} />);

    fireEvent.mouseMove(screen.getByLabelText("1 mise à jour"));

    expect(screen.getByRole("tooltip")).toHaveTextContent("La recette commence lundi");
  });

  it("referme l'infobulle quand la souris quitte la cellule", () => {
    render(<UpdatesCounter nombre={1} derniere={derniere()} maintenant={MAINTENANT} />);
    const compteur = screen.getByLabelText("1 mise à jour");

    fireEvent.mouseMove(compteur);
    fireEvent.mouseLeave(compteur);

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("compte sans infobulle si le dernier message manque", () => {
    render(<UpdatesCounter nombre={2} derniere={null} maintenant={MAINTENANT} />);

    fireEvent.mouseMove(screen.getByLabelText("2 mises à jour"));

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });
});

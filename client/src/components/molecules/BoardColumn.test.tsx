import { DndContext } from "@dnd-kit/core";
import { describe, expect, it } from "vitest";
import { render, screen, within } from "@testing-library/react";

import { BoardColumn } from "./BoardColumn";
import type { BoardCardResponse } from "@/lib/api/generated/model";

const carte = (id: number, label: string): BoardCardResponse =>
  ({
    project: {
      id,
      label,
      kind: "projet",
      statut: "realisation",
      parent_id: null,
      actif: true,
      estime_j: 20,
      categorie: "innover_differencier",
      date_mise_en_service: "2026-11-15",
      position: 0,
      monday_item_id: null,
      monday_subitem_id: null,
      is_syncable_to_monday: false,
      is_deletable: false,
    },
    consomme_j: 5,
    collaborateurs: [{ id: 1, display_name: "Léa Chen", initiales: "LC" }],
  }) as BoardCardResponse;

/** Les capteurs de @dnd-kit exigent un contexte englobant. */
const afficher = (cartes: BoardCardResponse[]) =>
  render(
    <DndContext>
      <BoardColumn statut="realisation" cartes={cartes} />
    </DndContext>,
  );

describe("BoardColumn", () => {
  it("annonce la phase et compte ses missions", () => {
    afficher([carte(1, "Portail bailleurs"), carte(2, "Refonte extranet")]);

    const colonne = screen.getByRole("region", { name: "Réalisation" });
    expect(within(colonne).getByRole("heading", { level: 2 })).toHaveTextContent(
      "Réalisation",
    );
    expect(within(colonne).getByText("2")).toBeInTheDocument();
  });

  it("affiche une carte par mission, dans l'ordre reçu", () => {
    afficher([carte(1, "Portail bailleurs"), carte(2, "Refonte extranet")]);

    const titres = screen.getAllByRole("heading", { level: 3 });
    expect(titres.map((titre) => titre.textContent)).toEqual([
      "Portail bailleurs",
      "Refonte extranet",
    ]);
  });

  it("invite au dépôt quand la phase est vide", () => {
    afficher([]);

    expect(screen.getByText("Aucune mission")).toBeInTheDocument();
    expect(screen.queryAllByRole("heading", { level: 3 })).toHaveLength(0);
  });

  it("n'affiche l'invite que sur une phase vide", () => {
    afficher([carte(1, "Portail bailleurs")]);

    expect(screen.queryByText("Aucune mission")).not.toBeInTheDocument();
  });

  it("ne place que des <li> dans la liste, sous peine de casser l'hydratation", () => {
    afficher([]);

    const liste = screen.getByRole("list");
    const intrus = [...liste.children].filter((noeud) => noeud.tagName !== "LI");
    expect(intrus).toEqual([]);
  });
});

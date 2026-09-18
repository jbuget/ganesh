import { DndContext } from "@dnd-kit/core";
import { describe, expect, it } from "vitest";
import { render, screen, within } from "@testing-library/react";

import { BoardColumn } from "./BoardColumn";
import type { BoardCardResponse } from "@/lib/api/generated/model";

const card = (id: number, label: string): BoardCardResponse =>
  ({
    project: {
      id,
      label,
      kind: "project",
      status: "development",
      parent_id: null,
      is_active: true,
      estimated_days: 20,
      category: "innovate_differentiate",
      go_live_date: "2026-11-15",
      position: 0,
      monday_item_id: null,
      monday_subitem_id: null,
      is_syncable_to_monday: false,
      is_deletable: false,
    },
    consumed_days: 5,
    contributors: [{ id: 1, display_name: "Léa Chen", initials: "LC" }],
  }) as BoardCardResponse;

/** Heure de reference figee : les apercus ne dependent pas de l'heure du run. */
const MAINTENANT = new Date("2026-09-16T11:00:00Z");

/** Les capteurs de @dnd-kit exigent un contexte englobant. */
const afficher = (cards: BoardCardResponse[], frozen = false) =>
  render(
    <DndContext>
      <BoardColumn
        status="development"
        cards={cards}
        maintenant={MAINTENANT}
        frozen={frozen}
      />
    </DndContext>,
  );

describe("BoardColumn", () => {
  it("annonce la phase et compte ses missions", () => {
    afficher([card(1, "Portail bailleurs"), card(2, "Refonte extranet")]);

    const column = screen.getByRole("region", { name: "Réalisation" });
    expect(within(column).getByRole("heading", { level: 2 })).toHaveTextContent(
      "Réalisation",
    );
    expect(within(column).getByText("2")).toBeInTheDocument();
  });

  it("affiche une carte par mission, dans l'ordre reçu", () => {
    afficher([card(1, "Portail bailleurs"), card(2, "Refonte extranet")]);

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

  it("distingue la phase par une pastille de couleur", () => {
    afficher([]);

    const titre = screen.getByRole("heading", { level: 2 });
    const dot = titre.querySelector("span");
    expect(dot).toHaveClass("bg-blue-500");
    // Decorative : elle double le titre, elle ne l'annonce pas deux fois.
    expect(dot).toHaveAttribute("aria-hidden");
  });

  it("garde son intitulé hors de la liste qui défile", () => {
    // Chaque colonne defile pour elle-meme : son titre doit rester en
    // vis-a-vis de celui des autres, quelle que soit sa pile de cartes.
    afficher([card(1, "Portail bailleurs")]);

    const defilante = screen.getByRole("list");

    expect(defilante).toHaveClass("overflow-y-auto");
    expect(defilante).not.toContainElement(screen.getByRole("heading", { level: 2 }));
  });

  it("n'affiche l'invite que sur une phase vide", () => {
    afficher([card(1, "Portail bailleurs")]);

    expect(screen.queryByText("Aucune mission")).not.toBeInTheDocument();
  });

  it("ne place que des <li> dans la liste, sous peine de casser l'hydratation", () => {
    afficher([]);

    const liste = screen.getByRole("list");
    const intrus = [...liste.children].filter((noeud) => noeud.tagName !== "LI");
    expect(intrus).toEqual([]);
  });
});

describe("colonne figée par un filtre", () => {
  it("retire la poignée : une carte filtrée ne se range plus", () => {
    afficher([card(1, "Portail bailleurs")], true);

    expect(screen.queryByRole("button", { name: /Déplacer/ })).toBeNull();
  });

  it("garde sa poignée hors filtre", () => {
    afficher([card(1, "Portail bailleurs")]);

    expect(
      screen.getByRole("button", { name: "Déplacer Portail bailleurs" }),
    ).toBeInTheDocument();
  });

  it("explique un vide dû aux filtres plutôt qu'un vide tout court", () => {
    afficher([], true);

    expect(
      screen.getByText("Aucune mission ne répond aux filtres"),
    ).toBeInTheDocument();
  });
});

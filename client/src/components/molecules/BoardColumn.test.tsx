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

/** Frozen reference time: previews do not depend on when the run happens. */
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
  it("announces the phase and counts its missions", () => {
    afficher([card(1, "Portail bailleurs"), card(2, "Refonte extranet")]);

    const column = screen.getByRole("region", { name: "Réalisation" });
    expect(within(column).getByRole("heading", { level: 2 })).toHaveTextContent(
      "Réalisation",
    );
    expect(within(column).getByText("2")).toBeInTheDocument();
  });

  it("shows one card per mission, in the order received", () => {
    afficher([card(1, "Portail bailleurs"), card(2, "Refonte extranet")]);

    const titres = screen.getAllByRole("heading", { level: 3 });
    expect(titres.map((titre) => titre.textContent)).toEqual([
      "Portail bailleurs",
      "Refonte extranet",
    ]);
  });

  it("invites a drop when the phase is empty", () => {
    afficher([]);

    expect(screen.getByText("Aucune mission")).toBeInTheDocument();
    expect(screen.queryAllByRole("heading", { level: 3 })).toHaveLength(0);
  });

  it("tells the phase apart by a coloured dot", () => {
    afficher([]);

    const titre = screen.getByRole("heading", { level: 2 });
    const dot = titre.querySelector("span");
    expect(dot).toHaveClass("bg-blue-500");
    // Decorative: it doubles the title, it does not announce it twice.
    expect(dot).toHaveAttribute("aria-hidden");
  });

  it("keeps its heading out of the scrolling list", () => {
    // Each column scrolls on its own: its title must stay level with the
    // others', whatever its stack of cards.
    afficher([card(1, "Portail bailleurs")]);

    const defilante = screen.getByRole("list");

    expect(defilante).toHaveClass("overflow-y-auto");
    expect(defilante).not.toContainElement(screen.getByRole("heading", { level: 2 }));
  });

  it("shows the prompt only on an empty phase", () => {
    afficher([card(1, "Portail bailleurs")]);

    expect(screen.queryByText("Aucune mission")).not.toBeInTheDocument();
  });

  it("puts only <li> in the list, on pain of breaking hydration", () => {
    afficher([]);

    const liste = screen.getByRole("list");
    const intrus = [...liste.children].filter((noeud) => noeud.tagName !== "LI");
    expect(intrus).toEqual([]);
  });
});

describe("a column frozen by a filter", () => {
  it("removes the handle: a filtered card no longer arranges", () => {
    afficher([card(1, "Portail bailleurs")], true);

    expect(screen.queryByRole("button", { name: /Déplacer/ })).toBeNull();
  });

  it("keeps its handle when unfiltered", () => {
    afficher([card(1, "Portail bailleurs")]);

    expect(
      screen.getByRole("button", { name: "Déplacer Portail bailleurs" }),
    ).toBeInTheDocument();
  });

  it("explains an emptiness caused by filters rather than a plain emptiness", () => {
    afficher([], true);

    expect(
      screen.getByText("Aucune mission ne répond aux filtres"),
    ).toBeInTheDocument();
  });
});

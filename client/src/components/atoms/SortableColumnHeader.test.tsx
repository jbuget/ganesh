import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { SortableColumnHeader } from "./SortableColumnHeader";
import { NO_SORT, type MissionSort } from "@/lib/mission-sort";

function afficher(sorted: MissionSort, onBasculer = vi.fn()) {
  render(
    <table>
      <thead>
        <tr>
          <SortableColumnHeader
            column="estimated"
            label="Estimé"
            sorted={sorted}
            onBasculer={onBasculer}
          />
        </tr>
      </thead>
    </table>,
  );
  return onBasculer;
}

describe("SortableColumnHeader", () => {
  it("demande le rangement sur sa colonne quand on la clique", () => {
    const onBasculer = afficher(NO_SORT);

    fireEvent.click(screen.getByRole("button", { name: /Estimé/ }));

    expect(onBasculer).toHaveBeenCalledWith("estimated");
  });

  it("n'annonce aucun ordre tant que la colonne ne range pas la liste", () => {
    afficher(NO_SORT);

    expect(screen.getByRole("columnheader")).toHaveAttribute("aria-sort", "none");
    expect(screen.queryByLabelText("Ordre croissant")).not.toBeInTheDocument();
  });

  it("montre le sens croissant quand elle range la liste", () => {
    afficher({ column: "estimated", direction: "asc" });

    expect(screen.getByRole("columnheader")).toHaveAttribute("aria-sort", "ascending");
    expect(screen.getByLabelText("Ordre croissant")).toBeInTheDocument();
  });

  it("montre le sens décroissant", () => {
    afficher({ column: "estimated", direction: "desc" });

    expect(screen.getByRole("columnheader")).toHaveAttribute("aria-sort", "descending");
    expect(screen.getByLabelText("Ordre décroissant")).toBeInTheDocument();
  });

  it("reste muette quand c'est une autre colonne qui range la liste", () => {
    // Two arrows shown at once would no longer say which one orders the list.
    afficher({ column: "phase", direction: "asc" });

    expect(screen.getByRole("columnheader")).toHaveAttribute("aria-sort", "none");
    expect(screen.queryByLabelText("Ordre croissant")).not.toBeInTheDocument();
  });
});

import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { SortableColumnHeader } from "./SortableColumnHeader";
import { AUCUN_TRI, type TriMissions } from "@/lib/mission-sort";

function afficher(tri: TriMissions, onBasculer = vi.fn()) {
  render(
    <table>
      <thead>
        <tr>
          <SortableColumnHeader
            colonne="estime"
            libelle="Estimé"
            tri={tri}
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
    const onBasculer = afficher(AUCUN_TRI);

    fireEvent.click(screen.getByRole("button", { name: /Estimé/ }));

    expect(onBasculer).toHaveBeenCalledWith("estime");
  });

  it("n'annonce aucun ordre tant que la colonne ne range pas la liste", () => {
    afficher(AUCUN_TRI);

    expect(screen.getByRole("columnheader")).toHaveAttribute("aria-sort", "none");
    expect(screen.queryByLabelText("Ordre croissant")).not.toBeInTheDocument();
  });

  it("montre le sens croissant quand elle range la liste", () => {
    afficher({ colonne: "estime", sens: "asc" });

    expect(screen.getByRole("columnheader")).toHaveAttribute("aria-sort", "ascending");
    expect(screen.getByLabelText("Ordre croissant")).toBeInTheDocument();
  });

  it("montre le sens décroissant", () => {
    afficher({ colonne: "estime", sens: "desc" });

    expect(screen.getByRole("columnheader")).toHaveAttribute("aria-sort", "descending");
    expect(screen.getByLabelText("Ordre décroissant")).toBeInTheDocument();
  });

  it("reste muette quand c'est une autre colonne qui range la liste", () => {
    // Deux fleches affichees en meme temps ne diraient plus laquelle ordonne.
    afficher({ colonne: "phase", sens: "asc" });

    expect(screen.getByRole("columnheader")).toHaveAttribute("aria-sort", "none");
    expect(screen.queryByLabelText("Ordre croissant")).not.toBeInTheDocument();
  });
});

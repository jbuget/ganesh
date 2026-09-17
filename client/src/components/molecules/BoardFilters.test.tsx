import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { BoardFilters } from "./BoardFilters";
import { AUCUN_FILTRE, type BoardFilters as Criteres } from "@/lib/board-filters";

vi.mock("@/lib/api/queries", () => ({
  useTeammates: () => ({
    teammates: [{ id: 3, display_name: "Nino Bosc", initiales: "NB" }],
  }),
}));

const barre = (over: Partial<Criteres> = {}, props: Record<string, unknown> = {}) => {
  const filtres = { ...AUCUN_FILTRE, ...over };
  const onChange = vi.fn();
  const onEffacer = vi.fn();
  render(
    <BoardFilters
      filtres={filtres}
      actif={
        filtres.nom !== "" ||
        filtres.phases.length > 0 ||
        filtres.categories.length > 0 ||
        filtres.priorites.length > 0 ||
        filtres.intervenants.length > 0 ||
        filtres.types.length > 0 ||
        filtres.etats.length > 0
      }
      onChange={onChange}
      onEffacer={onEffacer}
      visibles={3}
      total={12}
      {...props}
    />,
  );
  return { onChange, onEffacer };
};

describe("BoardFilters", () => {
  it("propose les cinq critères", () => {
    barre();

    expect(screen.getByLabelText("Rechercher une mission")).toBeInTheDocument();
    ["Phase", "Catégorie", "Priorité", "Intervenant", "Type", "État"].forEach(
      (critere) => {
        expect(
          screen.getByRole("button", { name: new RegExp(critere) }),
        ).toBeInTheDocument();
      },
    );
  });

  it("remonte la recherche saisie", () => {
    const { onChange } = barre();

    fireEvent.change(screen.getByLabelText("Rechercher une mission"), {
      target: { value: "portail" },
    });

    expect(onChange).toHaveBeenCalledWith({ nom: "portail" });
  });

  it("remonte une phase cochée", () => {
    const { onChange } = barre();

    fireEvent.click(screen.getByRole("button", { name: /Phase/ }));
    fireEvent.click(screen.getByRole("button", { name: "Réalisation" }));

    expect(onChange).toHaveBeenCalledWith({ phases: ["realisation"] });
  });

  it("remonte un intervenant coché, par son identifiant", () => {
    const { onChange } = barre();

    fireEvent.click(screen.getByRole("button", { name: /Intervenant/ }));
    fireEvent.click(screen.getByRole("button", { name: /Nino Bosc/ }));

    expect(onChange).toHaveBeenCalledWith({ intervenants: [3] });
  });

  it("distingue les projets des sous-projets", () => {
    const { onChange } = barre();

    fireEvent.click(screen.getByRole("button", { name: /Type/ }));
    fireEvent.click(screen.getByRole("button", { name: "Sous-projets" }));

    expect(onChange).toHaveBeenCalledWith({ types: ["lot"] });
  });

  it("remonte une priorité cochée", () => {
    const { onChange } = barre();

    fireEvent.click(screen.getByRole("button", { name: /Priorité/ }));
    fireEvent.click(screen.getByRole("button", { name: "Critique" }));

    expect(onChange).toHaveBeenCalledWith({ priorites: ["critique"] });
  });

  it("propose de consulter les missions archivées", () => {
    const { onChange } = barre();

    fireEvent.click(screen.getByRole("button", { name: /État/ }));
    fireEvent.click(screen.getByRole("button", { name: "Archivées" }));

    expect(onChange).toHaveBeenCalledWith({ etats: ["archivee"] });
  });

  it("n'offre d'effacer que lorsqu'il y a quelque chose à effacer", () => {
    barre();

    expect(screen.queryByRole("button", { name: "Effacer" })).toBeNull();
  });

  it("efface tous les critères d'un clic", () => {
    const { onEffacer } = barre({ nom: "portail" });

    fireEvent.click(screen.getByRole("button", { name: "Effacer" }));

    expect(onEffacer).toHaveBeenCalledTimes(1);
  });

  it("dit ce qu'on voit sur ce que le tableau porte", () => {
    barre({ phases: ["cadrage"] });

    expect(screen.getByText("3 missions sur 12")).toBeInTheDocument();
  });
});
